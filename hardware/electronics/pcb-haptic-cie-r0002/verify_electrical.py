"""Regenerate the native A3 rule, plot, schematic and independent connectivity evidence."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from check_artwork import HERE, STEM

sys.path.insert(0, str(HERE.parents[1] / "verification/r0012"))
import plot_review


def run(kicad):
    board = HERE / (STEM + ".kicad_pcb")
    schematic = board.with_suffix(".kicad_sch")
    original = HERE.with_name("pcb-haptic-cie-r0001") / "A3-CIE-R0001.kicad_pcb"
    drc = [kicad, "pcb", "drc", "--schematic-parity", "--all-track-errors",
           "--format", "json", "--exit-code-violations"]
    with tempfile.TemporaryDirectory() as temp:
        old = Path(temp) / "original.json"
        code = subprocess.run([*drc, "-o", str(old), str(original)]).returncode
        report = json.loads(old.read_bytes())
        pairs = [sorted(i["description"] for i in v["items"]) for v in report["violations"]]
        assert code == 5 and len(pairs) == 3 and all(v["type"] == "courtyards_overlap"
                                                      for v in report["violations"])
        assert sorted(pairs) == sorted([sorted(["Footprint J1", "Footprint " + n]) for n in ("C1", "U1", "R1")])
        assert not report["unconnected_items"] and not report["schematic_parity"]
    subprocess.run([*drc, "-o", str(HERE / "drc.json"), str(board)], check=True)
    subprocess.run([kicad, "sch", "erc", "--format", "json", "--exit-code-violations",
                    "-o", str(HERE / "erc.json"), str(schematic)], check=True)
    subprocess.run([kicad, "sch", "export", "netlist", "--format", "kicadxml",
                    "-o", str(HERE / "connectivity.xml"), str(schematic)], check=True)
    plot_review.BOARDS["A3"] = (HERE.name, STEM)
    plot_review.plot(kicad, "A3")
    result = subprocess.run([sys.executable, str(HERE / "check_artwork.py")], check=True,
                            stdout=subprocess.PIPE)
    (HERE / "artwork-verification.json").write_text(json.dumps(json.loads(result.stdout), indent=2) + "\n",
                                                   encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad", default="kicad-cli")
    run(parser.parse_args().kicad)
