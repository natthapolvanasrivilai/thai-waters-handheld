import copy
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import cadquery as cq
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from flat_exterior import audit, main


def box(x1, y1, z1, x2, y2, z2):
    return cq.Solid.makeBox(x2-x1, y2-y1, z2-z1, cq.Vector(x1, y1, z1))


REGION = {
    "name": "underside datum stock",
    "axis": "z", "plane_mm": 0, "outward": -1,
    "footprint_mm": [[0.5, 9.5], [0.5, 7.5]],
    "stock_depth_mm": 2.5,
    "allowed_protrusions": [],
    "stock_openings": [],
}


class FlatExteriorTest(unittest.TestCase):
    def setUp(self):
        self.stock = box(0, 0, 0, 10, 8, 2.5)
        self.r = copy.deepcopy(REGION)

    def test_clean_plane_passes_without_assuming_bbox(self):
        self.assertTrue(audit(self.stock, [self.r])["pass"])

    def test_four_tabs_fail_despite_unchanged_global_bounds_and_full_stock(self):
        shoe = box(0, 0, -1.2, 0.4, 8, .5)  # outside measured footprint
        tabs = [box(5, y, -.7, 6, y+.4, .2) for y in (1, 2.5, 4, 6)]
        clean = self.stock.fuse(shoe)
        bad = clean.fuse(*tabs)
        self.assertAlmostEqual(clean.BoundingBox().zmin, bad.BoundingBox().zmin)
        r = audit(bad, [self.r])
        self.assertFalse(r["pass"])
        q = r["regions"][0]
        self.assertEqual(q["unexpected_outer_solids"], 4)
        self.assertAlmostEqual(q["unexpected_outer_mm3"], 1.12, places=7)
        self.assertAlmostEqual(q["max_unexpected_height_mm"], .7, places=7)
        self.assertAlmostEqual(q["missing_stock_mm3"], 0, places=7)
        self.assertTrue(audit(clean, [self.r])["pass"])

    def test_overcut_does_not_pass_just_because_there_is_no_tab(self):
        bad = self.stock.cut(box(5, 4, -.4, 6, 5, .4))
        r = audit(bad, [self.r])
        self.assertFalse(r["pass"])
        self.assertAlmostEqual(r["regions"][0]["missing_stock_mm3"], .4, places=7)

    def test_declared_opening_and_protrusion_are_independent(self):
        bad = self.stock.cut(box(5, 4, -.4, 6, 5, 3)).fuse(box(7, 4, -.7, 8, 5, .2))
        self.r["allowed_protrusions"] = [
            {"name": "mating receiver", "reason": "controlled fit drawing", "footprint_mm": [[7, 8], [4, 5]], "max_height_mm": .7}
        ]
        self.assertFalse(audit(bad, [self.r])["pass"])
        self.r["stock_openings"] = [
            {"name": "service opening", "reason": "controlled aperture", "footprint_mm": [[5, 6], [4, 5]]}
        ]
        self.assertTrue(audit(bad, [self.r])["pass"])
        taller = bad.fuse(box(7, 4, -.8, 8, 5, .02))
        self.assertFalse(audit(taller, [self.r])["pass"])

    def test_positive_normal_and_wrong_or_empty_region(self):
        self.r.update(plane_mm=2.5, outward=1)
        self.assertTrue(audit(self.stock, [self.r])["pass"])
        with self.assertRaises(ValueError):
            audit(self.stock, [])
        self.r["footprint_mm"] = [[1, 1], [0, 1]]
        with self.assertRaises(ValueError):
            audit(self.stock, [self.r])
        self.r["footprint_mm"] = [[0.5, 9.5], [0.5, 7.5]]
        self.r["stock_openings"] = [
            {"name": "everything", "reason": "invalid all-coverage", "footprint_mm": self.r["footprint_mm"]}
        ]
        with self.assertRaises(ValueError):
            audit(self.stock, [self.r])

    def test_multiple_step_roots_cannot_pass_by_picking_a_clean_one(self):
        with TemporaryDirectory() as td:
            step = Path(td) / "unresolved.step"
            spec = Path(td) / "regions.json"
            spec.write_text(json.dumps({"regions": [self.r]}))
            writer = STEPControl_Writer()
            writer.Transfer(self.stock.wrapped, STEPControl_AsIs)
            writer.Transfer(box(5, 4, -.7, 6, 5, -.2).wrapped, STEPControl_AsIs)
            writer.Write(str(step))
            self.assertEqual(len(cq.importers.importStep(str(step)).vals()), 2)
            err = io.StringIO()
            with patch("sys.argv", ["flat_exterior.py", str(step), str(spec)]):
                with redirect_stdout(io.StringIO()), redirect_stderr(err):
                    self.assertEqual(main(), 2)
            self.assertIn("one STEP root", err.getvalue())


if __name__ == "__main__":
    unittest.main()
