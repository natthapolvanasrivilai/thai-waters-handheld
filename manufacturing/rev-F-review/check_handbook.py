"""Verify wiki navigation, software evidence paths and the two embedded applications."""
import base64
import csv
import gzip
import hashlib
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parents[2]
wiki = root / "docs/wiki"
book = (root / "docs/index.html").read_text(encoding="utf-8")
pages = [root / "README.md", *sorted(wiki.glob("*.md"))]
links = 0
tracked = subprocess.check_output(["git", "ls-files", "-z", "*.md"], cwd=root).decode().split("\0")
for page in (root / name for name in tracked if name):
    for href in re.findall(r"\[[^\]]*\]\(([^)]+)\)", page.read_bytes().decode("utf-8-sig", errors="replace")):
        dest = urlsplit(href)
        if dest.scheme or not dest.path:
            continue
        target = (page.parent / unquote(dest.path)).resolve()
        assert target.is_relative_to(root) and target.exists(), (page.name, href)
        links += 1
for chapter in wiki.glob("*.md"):
    assert chapter.name in (wiki / "Home.md").read_text(encoding="utf-8")
    if chapter.name != "Home.md":
        assert chapter.name in book, chapter.name
with (Path(__file__).parent / "software-evidence.csv").open(encoding="utf-8-sig", newline="") as source:
    for row in csv.DictReader(source):
        assert (root / row["Source"]).exists(), row["Source"]
for element in ("compressedGame", "compressedModel"):
    match = re.search(fr'<script id="{element}"[^>]*>([^<]+)</script>', book)
    payload = gzip.decompress(base64.b64decode(match[1]))
    assert b"<canvas" in payload or b"createElement('canvas')" in payload or b"WebGL" in payload
    if element == "compressedGame":
        assert payload == (root / "game/Thai-Waters-play.html").read_bytes()
    if element == "compressedModel":
        assert payload == (root / "docs/models/TW-A-0001-R0008-exploded.html").read_bytes()
    print(element, len(payload), hashlib.sha256(payload).hexdigest())
print(f"PASS {len(pages)} README/wiki pages, {links} local links across tracked Markdown, two embedded apps and all software evidence paths.")
