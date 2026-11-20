"""Exercise evidence publication with a fake solver, not circuit qualification."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify


class EvidencePublicationTests(unittest.TestCase):
    files = ("solver-evidence.zip", "results.csv", "verification.json")
    accepted = b"previously accepted evidence"

    def run_fixture(self, *, extra_failure=False, missing_control=False):
        readings = {
            ("diagnostic_no_cell_default", "pmic_v"): (4 if missing_control else 0, 3.9, 5.5),
            ("diagnostic_no_cell_configured", "pmic_v"): (0, 3.9, 5.5),
            ("diagnostic_no_cell_grant_loss", "pmic_v"): (0, 3.9, 5.5),
            ("diagnostic_previous_play_with_lamp", "port"): (1, 0, 0.5),
            ("diagnostic_mux_old_termination", "rise"): (1, 4e-9, 2e-8),
            ("candidate", "good"): (2 if extra_failure else 0.5, 0, 1),
        }
        by_case = {case: (metric, values) for (case, metric), values in readings.items()}

        def circuits():
            for case, (metric, (_, low, high)) in by_case.items():
                yield case, "Vone x 0 1", ".tran 1n 1u", [(metric, "max v(x)", "V", low, high)]

        def fake_run(cmd, **kwargs):
            metric, (value, _, _) = by_case[Path(cmd[-1]).stem]
            Path(cmd[cmd.index("-o") + 1]).write_text(f"Index time v(x)\n{metric} = {value}\n")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in self.files:
                (root / name).write_bytes(self.accepted)
            with (
                patch.object(verify, "HERE", root),
                patch.object(verify, "digest", return_value="54068911555d46067ff2bdfcd0cf4b1afd3c1330be0586f93911df0a6af88e7c"),
                patch.object(verify, "historical", return_value={}),
                patch.object(verify, "circuits", circuits),
                patch.object(verify.subprocess, "run", side_effect=fake_run),
                patch.object(sys, "argv", ["verify.py", "--engine", str(root / "fake-engine")]),
            ):
                try:
                    verify.main()
                except SystemExit as exc:
                    error = str(exc)
                else:
                    error = None
            return error, [(root / name).read_bytes() for name in self.files]

    def test_new_failure_preserves_evidence(self):
        error, contents = self.run_fixture(extra_failure=True)
        self.assertIn("('candidate', 'good')", error)
        self.assertEqual(contents, [self.accepted] * len(self.files))

    def test_missing_control_preserves_evidence(self):
        error, contents = self.run_fixture(missing_control=True)
        self.assertIn("missing negative controls: [('diagnostic_no_cell_default', 'pmic_v')]", error)
        self.assertEqual(contents, [self.accepted] * len(self.files))

    def test_expected_outcomes_publish_all_files(self):
        error, contents = self.run_fixture()
        self.assertIsNone(error)
        for content in contents:
            self.assertNotEqual(content, self.accepted)


if __name__ == "__main__":
    unittest.main()

