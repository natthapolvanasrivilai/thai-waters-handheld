"""Fail-closed local revision gate; publishing/ordering is deliberately absent."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

# Each ID represents a distinct reviewable test, not a marketing checkbox.
CHECKS = {
    "mechanical_fdm": (
        "native_cad_and_slice", "printability_and_cosmetics", "physical_dimensional_first_article"),
    "pcb": ("schematic_bom_erc", "layout_drc_and_populated_fit", "physical_bringup"),
    "power": ("hazard_review", "bench_limits_and_controls", "measured_faults_and_protection"),
    "software_firmware": (
        "build_compatibility_and_recovery", "target_regression_and_update", "physical_target_endurance"),
    "assembly": ("exact_interfaces_and_sequence", "fit_and_service_first_article", "repeatable_final_qc"),
    "packaging": ("configuration_and_traceability", "protection_and_labels", "distribution_validation"),
}
SAFETY = {"power.hazard_review"}
OWNER = "natthapolvanasrivilai"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def git(root, *args):
    return subprocess.check_output(("git", "-C", str(root), *args)).decode().strip()


def validate(doc, root, *, actual_private=False, evidence_sha="", reviews=()):
    def require(condition, msg):
        if not condition:
            raise ValueError(msg)

    require(isinstance(doc, dict) and doc.get("schema") == 1, "Unknown schema")
    stage, scope = doc.get("stage"), doc.get("scope")
    require(stage in ("prototype", "production"), "Invalid stage")
    require(scope in ("software-only", "inert", "powered"), "Invalid scope")
    require(stage != "production" or scope == "powered", "Full product production scope required")
    require(isinstance(doc.get("revision"), str) and re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{2,63}", doc["revision"]), "Invalid revision")
    source = doc.get("source_commit", "")
    require(isinstance(source, str) and HEX40.fullmatch(source), "Source SHA must be exact")
    require(git(root, "rev-parse", "HEAD") == evidence_sha, "Evidence checkout SHA mismatch")
    require(git(root, "merge-base", source, evidence_sha) == source and source != evidence_sha,
            "Exact source must precede the evidence commit")
    changed = subprocess.check_output(
        ("git", "-C", str(root), "diff", "--no-renames", "--name-only", "-z",
         source, evidence_sha)).decode().split("\0")
    require(all(p.startswith(("quality/revision-gates/", "verification/revision-evidence/"))
                for p in changed if p), "Product source changed in evidence commit")
    records = doc.get("checks", {})
    ids = {f"{d}.{name}" for d, items in CHECKS.items() for name in items}
    require(isinstance(records, dict) and set(records) == ids, "Missing/unknown check IDs")
    must_pass = set(SAFETY)
    if stage == "production":
        must_pass = ids
    else:
        must_pass |= {f"{d}.{items[0]}" for d, items in CHECKS.items()}
        if scope == "powered":
            must_pass |= {"power.bench_limits_and_controls", "power.measured_faults_and_protection", "pcb.layout_drc_and_populated_fit",
                          "assembly.fit_and_service_first_article"}
        if scope == "inert":
            must_pass |= {"mechanical_fdm.printability_and_cosmetics"}
        if scope == "software-only":
            must_pass -= {"mechanical_fdm.native_cad_and_slice", "pcb.schematic_bom_erc",
                          "assembly.exact_interfaces_and_sequence"}
    # Prototype N/A is only allowed for truly absent hardware. A postponed check is pending.
    absent_hardware = scope == "software-only"
    for name, row in records.items():
        require(isinstance(row, dict), f"{name}: invalid record")
        status = row.get("status")
        require(status in {"pass", "pending", "fail", "not-applicable"}, f"{name}: invalid status")
        require(isinstance(row.get("statement"), str) and len(row["statement"].strip()) >= 16,
                f"{name}: describe actual result, limitation, or scope rationale")
        require(name not in must_pass or status == "pass", f"{name}: required PASS")
        require(status != "fail", f"{name}: unresolved failure")
        applicable_na = absent_hardware and name.split(".")[0] in {
            "mechanical_fdm", "pcb", "assembly"}
        if scope == "inert" and name == "power.measured_faults_and_protection":
            applicable_na = True
        require(status != "not-applicable" or (stage == "prototype" and applicable_na),
                f"{name}: N/A not permitted for this scope")
        evidence = row.get("evidence")
        require(isinstance(evidence, list), f"{name}: explicit evidence list required")
        require(status != "pass" or evidence, f"{name}: PASS requires evidence")
        for ref in evidence:
            require(isinstance(ref, dict) and isinstance(ref.get("path"), str)
                    and isinstance(ref.get("sha256"), str) and HEX64.fullmatch(ref["sha256"]),
                    f"{name}: invalid evidence entry")
            p = Path(ref["path"])
            require(not p.is_absolute() and ".." not in p.parts
                    and p.parts[:2] == ("verification", "revision-evidence"),
                    f"{name}: evidence must be under verification/revision-evidence/")
            f = root / p
            require(f.is_file() and f.resolve().is_relative_to(root.resolve())
                    and not any((root / Path(*p.parts[:i])).is_symlink()
                                for i in range(1, len(p.parts)+1)),
                    f"{name}: evidence missing or symlinked")
            require(git(root, "cat-file", "-t", f"{evidence_sha}:{p.as_posix()}") == "blob",
                    f"{name}: evidence is not tracked in exact commit")
            committed = subprocess.check_output(("git", "-C", str(root), "show",
                                                  f"{evidence_sha}:{p.as_posix()}"))
            require(hashlib.sha256(committed).hexdigest() == ref["sha256"]
                    and hashlib.sha256(f.read_bytes()).hexdigest() == ref["sha256"],
                    f"{name}: exact evidence digest mismatch")

    if stage == "production":
        require(actual_private is True, "Production promotion and orders require a private repository")
        marker = f"release-gate: production {doc['revision']} {source}"
        # Most recent substantive owner review wins; comments cannot reset a rejection.
        owner_reviews = [r for r in reviews if r.get("user", {}).get("login") == OWNER
                         and r.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED")]
        latest = max(owner_reviews, key=lambda r: r.get("id", 0), default={})
        require(latest.get("state") == "APPROVED" and latest.get("commit_id") == evidence_sha
                and marker in (latest.get("body") or "").splitlines(),
                "Production requires current owner approval for exact evidence commit and source")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("manifest")
    p.add_argument("evidence_sha")
    p.add_argument("--github-facts", type=Path, help="Protected CI facts; not user-supplied attestations")
    a = p.parse_args()
    try:
        if not HEX40.fullmatch(a.evidence_sha):
            raise ValueError("Invalid evidence SHA")
        path = Path(a.manifest)
        if path.is_absolute() or ".." in path.parts or path.parts[:2] != (
             "quality", "revision-gates") or path.suffix != ".json":
            raise ValueError("Manifest must be tracked JSON under quality/revision-gates/")
        manifest = subprocess.check_output(("git", "-C", str(a.root), "show",
                                             f"{a.evidence_sha}:{path.as_posix()}"))
        facts = json.loads(a.github_facts.read_text()) if a.github_facts else {}
        validate(json.loads(manifest), a.root, actual_private=facts.get("private"),
                 evidence_sha=a.evidence_sha, reviews=facts.get("reviews", []))
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError) as exc:
        print("REVISION GATE BLOCKED:", exc, file=sys.stderr)
        return 1
    print("REVISION EVIDENCE PASSED. No promotion, publication, power-on or order was performed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
