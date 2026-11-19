"""Collect the versioned sources and tested engineering exports into an offline handoff."""
import argparse
import hashlib
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("outputs", type=Path)
out = parser.parse_args().outputs.resolve()
archive = out / "Thai-Waters-Rev-F-engineering-pack.zip"
files = {}
for name in (
    "Riffle-Rev-F-engineering-review.html", "Riffle-Rev-F-production-review.pdf",
    "Riffle-Rev-F-exploded.html", "Riffle-Rev-F-dressed-assembly.step.gz",
    "Riffle-Rev-F-exploded-preview.png", "Thai-Waters-Rev-F-grip.png",
    "Riffle-Rev-F-prototype.zip", "Riffle-Rev-F-battery-fit-gauges.zip",
    "Thai-Waters-firmware-0.7.zip", "Thai-Waters-ambient-review.png",
):
    files[name] = out / name
for name in (
    "hardware/verification", "hardware/mechanical/rev-F/review", "hardware/mechanical/experiments/reel-brake",
    "hardware/electronics", "manufacturing", "sourcing/production-intent", "commercial",
    "verification/firmware-0.6", "verification/firmware-0.7", "compliance", "docs/wiki", "service",
):
    directory = root / name
    assert directory.is_dir(), name
    for path in sorted(directory.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            files[path.relative_to(root).as_posix()] = path
assert len([p for p in files if p.startswith("hardware/verification/circuits/decks/") and p.endswith(".cir")]) == 42
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=5) as bundle:
    checksums = []
    for name, path in sorted(files.items()):
        data = path.read_bytes()
        bundle.writestr(name, data)
        checksums.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
    bundle.writestr("SHA256SUMS.txt", "\n".join(checksums) + "\n")
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
print(archive, archive.stat().st_size, len(files), hashlib.sha256(archive.read_bytes()).hexdigest())
