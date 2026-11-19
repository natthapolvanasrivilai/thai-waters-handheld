"""Rebuild the private art register in stable catalog order."""
import csv
import json
from pathlib import Path

base = Path(__file__).resolve().parent
content = base.parent / "content"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

catalog = read(content / "catalog.json")["fish"] + read(content / "extended.json")
sources = {}
for i in range(60):
    if i < 48:
        sources[i] = (f"plate-{i // 8}.png", 1 + i % 8)
    elif i < 52:
        sources[i] = ("plate-6.png", i - 47)
    else:
        sources[i] = ("plate-7.png", i - 51)
for plate in read(base / "field" / "plates.json"):
    for cell, (i, name) in enumerate(zip(plate["ids"], plate["species"]), 1):
        assert i not in sources and catalog[i]["name"] == name
        sources[i] = ("field/" + plate["file"], cell)
with (base / "coverage.csv").open("w", encoding="utf-8", newline="") as out:
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["catalog_id", "name", "portrait", "source_plate", "cell", "identification_review"])
    for i, record in enumerate(catalog):
        source, cell = sources.get(i, ("", ""))
        status = "individual" if source else "awaiting artwork"
        review = "pending" if source else ""
        if 52 <= i < 60:
            review = "fictional design"
        if record["name"] == "Gobiodon citrinus":
            review = "revise head bars; see artwork README"
        writer.writerow([i, record["name"], status, source, cell, review])
print(f"{len(sources)} individual portraits; {len(catalog) - len(sources)} awaiting artwork")
