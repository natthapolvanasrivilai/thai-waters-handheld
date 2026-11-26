"""Plot review Gerbers and Excellon from the native boards. Never writes to the historical releases."""
import argparse
import subprocess
import tempfile
import zipfile
from pathlib import Path

BOARDS = {"A3": ("pcb-haptic-cie-r0001", "A3-CIE-R0001"),
          "A4": ("pcb-r0004", "harness"), "A5": ("pcb-power-r0004", "usb-input")}
ELECTRONICS = Path(__file__).resolve().parents[2] / "electronics"
LAYERS = "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,Edge.Cuts"

def plot(kicad, label):
    directory, stem = BOARDS[label]
    folder = ELECTRONICS / directory
    board = folder / (stem + ".kicad_pcb")
    with tempfile.TemporaryDirectory() as scratch:
        fab = Path(scratch) / "fab"
        fab.mkdir()
        for options in (["gerbers", "--layers", LAYERS, "--no-protel-ext"],
                        ["drill", "--excellon-units", "mm"]):
            subprocess.run([kicad, "pcb", "export", *options, "-o", str(fab), str(board)], check=True)
        outputs = sorted(fab.iterdir())
        assert {p.suffix for p in outputs} == {".gbr", ".gbrjob", ".drl"}
        assert len(outputs) == 10
        with zipfile.ZipFile(folder / (stem + "-fab.zip"), "w", zipfile.ZIP_DEFLATED) as archive:
            for path in outputs:
                archive.write(path, path.name)
        subprocess.run([kicad, "sch", "export", "pdf", "-o", str(folder/"circuit.pdf"),
                        str(folder/(stem + ".kicad_sch"))], check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kicad", required=True)
    parser.add_argument("boards", nargs="+", choices=BOARDS)
    args = parser.parse_args()
    for board in args.boards:
        plot(args.kicad, board)

