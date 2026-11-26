import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from revision_gate import CHECKS, OWNER, validate
from release_handbook import digest, render


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
        for prefix in ("docs/wiki", "docs/release-handbook-public"):
            hm = cls.root / prefix / "Home.md"
            hm.parent.mkdir(parents=True)
            hm.write_text(f"# Offline fixture guide: {len(prefix)} test edition\nUse safely. <script src='https://invalid.example'></script>\n")
        git("add", ".")
        git("commit", "-m", "source")
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

    def run_gate(self, d, private=False, reviews=(), snapshot_change=None, asset_change=None):
        def git(*a):
            return subprocess.check_output(("git", "-C", str(self.root), *a)).decode().strip()

        revision = d["revision"]
        name = f"Pocket-Reel-Handbook-0.9.4-{revision}.html"
        path = f"verification/revision-evidence/handbooks/{name}"
        f = self.root / path
        d["handbook"] = dict(release_version="0.9.4", release_tag="v0.9.4",
                             hardware_revision="R0009", firmware_revision="FW0.9.4", software_revision="SW0.9.4",
                             edition="public", changes=["Documented prototype revision change."],
                             path=path, asset_name=name)
        data = render(self.root, d)
        assert b"&lt;script" in data and b"Firmware</dt><dd>FW0.9.4" in data
        if snapshot_change == "wrong-firmware":
            d["handbook"]["firmware_revision"] = "FW0.9.3"
        if snapshot_change == "missing-firmware":
            del d["handbook"]["firmware_revision"]
        if snapshot_change == "unexplained-na":
            d["handbook"]["firmware_revision"] = "none"
        if snapshot_change == "stale":
            data = data.replace(b"Documented prototype revision change.", b"Older noncurrent revision change.")
        if snapshot_change != "missing":
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
            git("add", path)
        d["handbook"]["sha256"] = digest(data)
        if snapshot_change == "wrong-hash":
            d["handbook"]["sha256"] = "0" * 64
        if snapshot_change == "stale-evidence":
            d["checks"]["packaging.distribution_validation"]["status"] = "pending"
        if snapshot_change == "private-edition":
            d["handbook"]["edition"] = "owner-private"
        git("commit", "--allow-empty", "-m", "snapshot")
        newest = git("rev-parse", "HEAD")
        if reviews:
            reviews = [r | {"commit_id": newest} if r["commit_id"] == self.sha else r for r in reviews]
        asset = dict(tag_name="v0.9.4", tag_commit=d["source_commit"], draft=True,
                     prerelease=d["stage"]=="prototype", name=name, sha256=digest(data))
        if asset_change:
            asset.update(asset_change)
        try:
            validate(d, self.root, evidence_sha=newest, actual_private=private, reviews=reviews,
                     release_asset=None if asset_change == {} else asset)
        finally:
            git("reset", "--mixed", self.sha)
            f.unlink(missing_ok=True)

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

    def test_handbook_missing_stale_and_wrong_hash_are_blocking(self):
        for flag, error in (("missing", "missing tracked"), ("stale", "stale/mismatched"),
                            ("stale-evidence", "stale/mismatched"), ("wrong-firmware", "stale/mismatched"),
                            ("missing-firmware", "firmware_revision"), ("unexplained-na", "explain why"),
                            ("wrong-hash", "checksum")):
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, error):
                self.run_gate(self.doc(), snapshot_change=flag)

    def test_draft_asset_required_both_stages(self):
        for stage, scope in (("prototype", "inert"), ("production", "powered")):
            for change in ({}, {"name": "another.html"}, {"sha256": "0"*64}, {"draft": False}):
                with self.subTest(stage=stage, change=change), self.assertRaisesRegex(ValueError, "draft asset"):
                    self.run_gate(self.doc(stage, scope), True, [self.review()], asset_change=change)

    def test_stale_tag_source_or_wrong_tag_blocks(self):
        for change in ({"tag_commit": "1"*40}, {"tag_name": "prior"}):
            with self.assertRaisesRegex(ValueError, "tag does not resolve"):
                self.run_gate(self.doc(), asset_change=change)

    def test_private_handbook_never_allowed_in_public_repo(self):
        with self.assertRaisesRegex(ValueError, "owner-private handbook"):
            self.run_gate(self.doc(), snapshot_change="private-edition")

    def test_public_handbook_rejects_copy_and_links_into_private_edition(self):
        def git(*a):
            return subprocess.check_output(("git", "-C", str(self.root), *a)).decode().strip()
        p = self.root / "docs/release-handbook-public/Home.md"
        for data in ((self.root / "docs/wiki/Home.md").read_bytes(),
                     b"# Public fixture\n[Go to private chapter](../wiki/Home.md)"):
            p.write_bytes(data)
            git("add", str(p))
            git("commit", "--allow-empty", "-m", "bad edition")
            d = self.doc() | {"source_commit": git("rev-parse", "HEAD"),
                              "handbook": {"edition": "public"}}
            try:
                with self.assertRaisesRegex(ValueError, "private-edition source or link"):
                    render(self.root, d)
            finally:
                git("reset", "--hard", self.sha)

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
