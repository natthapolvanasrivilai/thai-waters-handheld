"""Public-safe synthetic slicer output; no printer commands are executed."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
import zipfile

TOOL = Path(__file__).resolve().parents[1] / "verify_model_extrusion.py"

SETTINGS = """<config>
<object id="1"><metadata key="name" value="Sample-Tab"/></object>
<plate><metadata key="plater_id" value="1"/>
<model_instance><metadata key="object_id" value="1"/>
<metadata key="identify_id" value="101"/></model_instance>
</plate></config>"""
FEATURE = {"plate": 1, "object_id": "101", "name": "right tab",
           "reference": "synthetic drawing, unbroken vertical tab",
           "xy_mm": [[9.3, 11.0], [0.9, 1.1]],
           "required_layers_z_mm": [1.0, 1.2], "minimum_path_mm": 0.6}


def layer(z, feature="Outer wall", model=True, local=False):
    s = f"; CHANGE_LAYER\n; Z_HEIGHT: {z}\n; LAYER_HEIGHT: 0.2\n; OBJECT_ID: 101\n"
    if feature:
        s += f"; FEATURE: {feature}\n"
    if model:
        s += "G0 X0 Y1\nG1 X2 E0.2\n"
    if local:
        s += "G0 X8 Y1\nG1 X12 E0.3\n"
    return s


class ExtrusionGuardTests(unittest.TestCase):
    def audit(self, gcode, *, spec=None, native_warning="", archive_metadata=SETTINGS, mesh=None,
              archive_plate=True, extra_args=()):
        report = {"return_code": 0, "sliced_plates": [{"id": 1, "warning_message": native_warning,
                  "objects": mesh or [{"name": "Sample-Tab", "bbox": {"z": 0, "height": 1.2}}]}]}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "result.json").write_text(json.dumps(report), encoding="utf-8")
            with zipfile.ZipFile(p / "Output.3mf", "w") as f:
                f.writestr("Metadata/model_settings.config", archive_metadata)
                if archive_plate:
                    f.writestr("Metadata/plate_1.gcode", gcode)
            cmd = [sys.executable, str(TOOL), str(p / "Output.3mf"), str(p / "result.json")]
            if spec is not None:
                (p / "features.json").write_text(json.dumps({"features": spec}), encoding="utf-8")
                cmd += ["--features", str(p / "features.json")]
            r = subprocess.run([*cmd, *extra_args], capture_output=True, text=True, check=False)
        self.assertTrue(r.stdout, r.stderr)
        return r.returncode, json.loads(r.stdout)

    def test_warning_free_truncation_is_a_hold_even_with_support_above_it(self):
        good_base = "G90\nM83\n" + "".join(layer(z) for z in [0.2, 0.4, 0.6])
        support = layer(0.8, "Support") + layer(1.0, "Brim") + layer(1.2, "Support interface")
        rc, result = self.audit(good_base + support)
        self.assertEqual(rc, 1)
        obj = result["objects"][0]
        self.assertEqual(obj["model_top_mm"], 0.6)
        self.assertEqual(obj["status"], "hold")

    def test_full_height_on_other_side_does_not_cover_missing_feature(self):
        gcode = "G90\nM83\n" + "".join(layer(z, local=(z == 1.0)) for z in [0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
        rc, result = self.audit(gcode + layer(1.2, "Support", False, True), spec=[FEATURE])
        self.assertEqual(rc, 1)
        self.assertEqual(result["objects"][0]["status"], "pass")
        self.assertEqual([m["path_mm"] for m in result["features"][0]["layers"]], [1.7, 0.0])

    def test_green_uses_actual_supported_object_roles_and_has_repro_identity(self):
        gcode = "G90\nM83\n" + "".join(layer(z, feature="Outer wall" if z == 0.2 else "", local=z >= 1.0)
                                       for z in [0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
        rc, result = self.audit(gcode, spec=[FEATURE])
        self.assertEqual(rc, 0)
        self.assertEqual(result["objects"][0]["model_bottom_mm"], 0.0)
        self.assertEqual(result["objects"][0]["model_layers"], 6)
        self.assertEqual(result["features"][0]["status"], "pass")
        self.assertEqual(len(result["inputs"]["sliced_3mf_sha256"]), 64)

    def test_absolute_e_does_not_count_feed_only_move_retraction_or_flat_travel(self):
        gcode = "G90\nM82\nG92 E0\n" + layer(0.2)
        # Positive absolute E coordinates are not necessarily extrusion.
        gcode += "; CHANGE_LAYER\n; Z_HEIGHT: 1.2\n; LAYER_HEIGHT: 0.2\n; OBJECT_ID: 101\n"
        gcode += "G1 X12 E0.2\nG1 X11 E0.1\nG1 E0.2\n"
        rc, report = self.audit(gcode)
        self.assertEqual(rc, 1)
        self.assertEqual(report["objects"][0]["model_top_mm"], 0.2)

    def test_arc_without_xy_endpoints_is_a_complete_local_circle(self):
        # Full CW circle, radius 1 at (10,1), relative extrusion.
        gcode = "G90\nM83\n" + "".join(layer(z) for z in [.2,.4,.6,.8,1])
        gcode += layer(1.2, model=False) + "G0 X11 Y1\nG2 I-1 J0 E0.4\n"
        f = {**FEATURE, "xy_mm": [[8.95, 11.05], [-.05, 2.05]],
             "required_layers_z_mm": [1.2], "minimum_path_mm": 6.0}
        rc, result = self.audit(gcode, spec=[f])
        self.assertEqual(rc, 0)
        self.assertAlmostEqual(result["features"][0]["layers"][0]["path_mm"], 6.283185, places=5)

    def test_late_start_and_overshoot_are_not_validated_by_top_only(self):
        rc, report = self.audit("M83\n" + layer(.8) + layer(1.4), extra_args=("--height-tolerance-mm", "0.1"))
        self.assertEqual(rc, 1)
        obj = report["objects"][0]
        self.assertAlmostEqual(obj["model_bottom_mm"], 0.6)
        self.assertAlmostEqual(obj["model_top_mm"], 1.4)

    def test_missing_archive_layer_or_ambiguous_identity_is_unverified(self):
        rc, report = self.audit("", archive_plate=False)
        self.assertEqual(rc, 2)
        self.assertEqual(report["status"], "unverified")
        rc, report = self.audit("M83\n" + layer(.2), mesh=[
            {"name": "Sample-Tab", "bbox": {"z": 0, "height": 1.2}},
            {"name": "Sample-Tab", "bbox": {"z": 0, "height": 1.2}}],
        )
        self.assertEqual(rc, 2)
        self.assertEqual(report["status"], "unverified")

    def test_fake_or_stale_object_cannot_be_attributed(self):
        gcode = "M83\n" + layer(.2) + layer(.4)
        gcode += "; CHANGE_LAYER\n; Z_HEIGHT: 1.2\n; LAYER_HEIGHT: 0.2\nG1 X9 Y1 E1\n"
        rc, result = self.audit(gcode)
        self.assertEqual(rc, 1)
        self.assertEqual(result["objects"][0]["model_top_mm"], .4)

    def test_unknown_deposition_role_is_unverified(self):
        rc, report = self.audit("M83\n" + layer(.2, feature="Vendor extension"))
        self.assertEqual(rc, 2)
        self.assertEqual(report["status"], "unverified")

    def test_adaptive_heights_at_same_layer_count_once_and_include_lower_model_interval(self):
        gcode = "G90\nM83\n" + layer(0.2)
        # Native generators can switch role/height within the same Z marker.
        gcode += "; LAYER_HEIGHT: 0.04\n; FEATURE: Top surface\nG1 X4 E0.2\n"
        gcode += layer(1.2)
        rc, report = self.audit(gcode)
        self.assertEqual(rc, 0)
        self.assertEqual(report["objects"][0]["model_layers"], 2)
        self.assertEqual(report["objects"][0]["model_bottom_mm"], 0)

    def test_native_next_label_precedes_previous_object_stop(self):
        gcode = "G90\nM83\n" + layer(.2)
        gcode += layer(1.2, model=False)
        gcode += "; stop printing object, unique label id: 999\n"
        gcode += "; start printing object, unique label id: 101\n"
        gcode += "G0 X0 Y1\nG1 X3 E0.2\n"
        rc, report = self.audit(gcode)
        self.assertEqual(rc, 0)
        self.assertEqual(report["objects"][0]["model_top_mm"], 1.2)

    def test_retract_recovery_motion_cannot_impersonate_a_local_feature(self):
        gcode = "G90\nM83\n" + layer(.2) + layer(1.0,local=True) + layer(1.2, model=False)
        gcode += "G0 X8 Y1\nG1 E-1\nG1 X12 E1\n"
        rc, result = self.audit(gcode, spec=[FEATURE])
        self.assertEqual(rc, 1)
        self.assertEqual(result["features"][0]["layers"][-1]["path_mm"], 0.0)
        self.assertEqual(result["objects"][0]["model_top_mm"], 1.0)

    def test_partial_recovery_counts_only_motion_after_extrusion_resumes(self):
        f = {**FEATURE, "xy_mm": [[9.8, 10.4], [0.9, 1.1]],
             "required_layers_z_mm": [1.2], "minimum_path_mm": .5}
        gcode = "G90\nM83\n" + layer(.2) + layer(1.2, model=False)
        gcode += "G0 X8 Y1\nG1 E-0.5\nG1 X12 E1\n"
        rc, result = self.audit(gcode, spec=[f])
        self.assertEqual(rc, 1)
        self.assertAlmostEqual(result["features"][0]["layers"][0]["path_mm"], 0.4)

    def test_g92_and_role_switch_do_not_clear_retract_debt(self):
        gcode = "G90\nM82\nG92 E0\n" + layer(.2)
        gcode += layer(1.2, "Support", model=False)
        gcode += "G1 E-0.8\nG92 E0\nG1 E0.4\n; FEATURE: Outer wall\nG0 X8 Y1\nG1 X12 E1.0\n"
        rc, result = self.audit(gcode, spec=[{**FEATURE, "required_layers_z_mm": [1.2]}])
        self.assertEqual(rc, 1)
        self.assertEqual(result["features"][0]["layers"][0]["path_mm"], 0.0)

    def test_tool_or_firmware_retract_change_in_model_job_is_unverified(self):
        for control in ("G10", "G11", "T1"):
            with self.subTest(control=control):
                gcode = "G90\nM83\nT0\n" + layer(.2) + control + "\n" + layer(1.2)
                self.assertEqual(self.audit(gcode)[0], 2)

    def test_model_motion_without_explicit_extrusion_mode_is_unverified(self):
        rc, result = self.audit("G90\n" + layer(.2) + layer(1.2))
        self.assertEqual(rc, 2)
        self.assertIn("mode", result["reason"])

    def test_unsupported_extrusion_spline_is_not_silently_ignored(self):
        gcode = "M83\nG28\nG90\nG4 P50\n" + layer(.2) + layer(1.2, local=True)
        gcode += "G5 X2 Y1 I1 J0 P-1 Q0 E1\n"
        rc, result = self.audit(gcode)
        self.assertEqual(rc, 2)
        self.assertIn("G5", result["reason"])

    def test_unsupported_absolute_arc_center_mode_fails_closed(self):
        gcode = "G90\nM83\n" + layer(.2) + layer(1.2, model=False)
        gcode += "G90.1\nG0 X11 Y1\nG2 I-1 J0 E0.4\n"
        rc, result = self.audit(gcode)
        self.assertEqual(rc, 2)
        self.assertIn("G90.1", result["reason"])

    def test_warned_plate_not_accepted_by_geometry_only(self):
        gcode = "G90\nM83\n" + layer(.2) + layer(1.2)
        rc, report = self.audit(gcode, native_warning="out of bounds")
        self.assertEqual(rc, 1)
        self.assertEqual(report["status"], "hold")


if __name__ == "__main__":
    unittest.main()
