import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from revision_gate import CHECKS, OWNER, validate


class GateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        def git(*a):
            return subprocess.check_output(("git", "-C", cls.tmp.name, *a),
                                           stderr=subprocess.DEVNULL).decode().strip()
        git("init")
        git("config", "user.name", "Fixture")
        git("config", "user.email", "fixture@example.invalid")
        git("commit", "--allow-empty", "-m", "source")
        cls.source = git("rev-parse", "HEAD")
        p = Path("verification/revision-evidence/test.txt")
        cls.file = cls.root / p
        data = b"Fixture only, never real evidence."
        cls.file.parent.mkdir(parents=True)
        cls.file.write_bytes(data)
        cls.ref = dict(path=str(p), sha256=hashlib.sha256(data).hexdigest())
        git("add", ".")
        git("commit", "-m", "evidence")
        cls.sha = git("rev-parse", "HEAD")

    def doc(self, stage="prototype", scope="inert"):
        return dict(schema=1, stage=stage, scope=scope, revision="TW-TEST",
                    source_commit=self.source,
                    checks={f"{d}.{k}": dict(status="pass",
                                             statement="Synthetic test record only.",
                                             evidence=[self.ref.copy()])
                            for d, keys in CHECKS.items() for k in keys})

    def run_gate(self, d, private=False, reviews=()):
        validate(d, self.root, evidence_sha=self.sha, actual_private=private, reviews=reviews)

    def review(self, **changes):
        r = dict(id=1, state="APPROVED", user={"login": OWNER}, commit_id=self.sha,
                 body=f"release-gate: production TW-TEST {self.source}")
        return r | changes

    def set_status(self, d, name, status):
        d["checks"][name].update(status=status, evidence=[])

    def test_public_prototype_allowed(self):
        self.run_gate(self.doc())

    def test_software_only_absence_allowed(self):
        d = self.doc(scope="software-only")
        self.set_status(d, "pcb.schematic_bom_erc", "not-applicable")
        self.run_gate(d)

    def test_proto_minimum_in_each_discipline(self):
        for area, keys in CHECKS.items():
            with self.subTest(area=area):
                d = self.doc()
                self.set_status(d, f"{area}.{keys[0]}", "pending")
                with self.assertRaisesRegex(ValueError, "required PASS"): self.run_gate(d)

    def test_powered_proto_needs_bench_controls(self):
        d = self.doc(scope="powered")
        self.set_status(d, "power.bench_limits_and_controls", "pending")
        with self.assertRaisesRegex(ValueError, "required PASS"): self.run_gate(d)

    def test_inert_proto_needs_native_printability(self):
        d = self.doc()
        self.set_status(d, "mechanical_fdm.printability_and_cosmetics", "pending")
        with self.assertRaisesRegex(ValueError, "required PASS"): self.run_gate(d)

    def test_inert_nonapplicable_does_not_skip_hazard_review(self):
        d = self.doc()
        self.set_status(d, "power.hazard_review", "not-applicable")
        with self.assertRaisesRegex(ValueError, "required PASS"): self.run_gate(d)

    def test_production_private_current_review(self):
        self.run_gate(self.doc("production", "powered"), True, [self.review()])

    def test_public_production_denied_even_with_review(self):
        with self.assertRaisesRegex(ValueError, "private"):
            self.run_gate(self.doc("production", "powered"), False, [self.review()])

    def test_production_rejects_stale_or_non_owner_or_later_rejection(self):
        d = self.doc("production", "powered")
        for reviews in ([self.review(commit_id=self.source)],
                        [self.review(user={"login": "Other"})],
                        [self.review(), self.review(id=2, state="CHANGES_REQUESTED")]):
            with self.assertRaisesRegex(ValueError, "owner approval"):
                self.run_gate(d, True, reviews)

    def test_manifest_self_approval_ignored(self):
        d = self.doc("production", "powered") | {"private": True, "owner_approved": True}
        with self.assertRaisesRegex(ValueError, "owner approval"): self.run_gate(d, True)

    def test_production_denies_pending_and_na(self):
        for status in ("pending", "not-applicable"):
            d = self.doc("production", "powered")
            self.set_status(d, "packaging.distribution_validation", status)
            with self.assertRaisesRegex(ValueError, "required PASS"):
                self.run_gate(d, True, [self.review()])

    def test_no_unknown_check_or_missing_check(self):
        d = self.doc()
        d["checks"].pop("power.hazard_review")
        with self.assertRaisesRegex(ValueError, "Missing/unknown"): self.run_gate(d)

    def test_tampered_digest_and_path_traversal(self):
        for ref, msg in [({"sha256": "0"*64}, "digest"),
                         ({"path": "verification/revision-evidence/../../secret"}, "under verification")]:
            d = self.doc()
            d["checks"]["power.hazard_review"]["evidence"][0].update(ref)
            with self.assertRaisesRegex(ValueError, msg): self.run_gate(d)

    def test_evidence_commit_cannot_alter_product(self):
        d = self.doc()
        original = self.sha
        def git(*args):
            return subprocess.check_output(("git", "-C", str(self.root), *args)).decode().strip()
        (self.root / "product.py").write_text("changed")
        git("add", "product.py")
        git("commit", "-m", "altered candidate")
        self.sha = git("rev-parse", "HEAD")
        try:
            with self.assertRaisesRegex(ValueError, "source changed"): self.run_gate(d)
        finally:
            git("reset", "--hard", original)
            del self.sha

    def test_pass_without_evidence(self):
        d = self.doc()
        self.set_status(d, "power.hazard_review", "pass")
        with self.assertRaisesRegex(ValueError, "requires evidence"): self.run_gate(d)

    def test_worktree_cannot_replace_exact_tracked_bytes(self):
        original = self.file.read_bytes()
        self.file.write_bytes(b"different checkout")
        try:
            with self.assertRaisesRegex(ValueError, "digest"): self.run_gate(self.doc())
        finally:
            self.file.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
