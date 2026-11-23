"""Inspect bed contact, support and component backing on every native project instance."""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pocket-reel-r19b-removal-trial"))
from path_evidence import inspect

def main(folder):
    rows = json.loads((HERE / "deposition.json").read_text())["objects"]
    report = []
    for plate in sorted({r["plate"] for r in rows}):
        items = [r for r in rows if r["plate"] == plate]
        paths, _ = inspect(folder / f"plate_{plate}.gcode", track_layers=True,
                           focus={r["object_id"] for r in items})
        for item in items:
            row = paths[item["object_id"]]
            report.append(dict(plate=plate, name=item["name"], **row))
        print("Checked plate", plate, flush=True)
    (HERE / "part-paths.json").write_text(json.dumps(report, indent=2) + "\n")

if __name__ == "__main__":
    main(Path(sys.argv[1]))
