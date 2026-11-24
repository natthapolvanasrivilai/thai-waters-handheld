"""Validate the live handbook and stamp its offline snapshot only when packaging a release."""
import argparse
import base64
import csv
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STATUS = "docs/wiki/Current-status.md"
BOOK = ROOT / "docs/index.html"
PANEL = ROOT / "docs/handbook/live-panel.html"
ASSEMBLY = ROOT / "hardware/mechanical/enclosure-fit-r0003/Enclosure-fit-guide.html"
ASSEMBLY_MARK = "@@PCB_ASSEMBLY@@"
MARK = "@@SNAPSHOT@@"
START = "<!-- Start live handbook -->"
END = "<!-- End live handbook -->"
PROJECT = "https://github.com/natthapolvanasrivilai/thai-waters-handheld/"
SOURCES = re.compile(
    r"^(hardware/revisions/assemblies\.csv|quality/(hardware-gate|hardware-review-[^/]+|seated-connector-review)\.md|"
    r"hardware/mechanical/[^/]+/(FIRST-ARTICLE\.csv|QA/[^/]*first-print/README\.md)|"
    r"hardware/mechanical/pcb-fit-[^/]+/README\.md|docs/wiki/Software-and-tests\.md|releases/README\.md)$"
)


def validate_record(markdown):
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    if len(lines) < 4 or lines[0] != "# Project status" or not re.fullmatch(r"Reviewed \d{4}-\d{2}-\d{2}", lines[1]):
        raise ValueError("Missing project title or ISO review date")
    date.fromisoformat(lines[1][9:])
    if not any(line.startswith("## ") for line in lines):
        raise ValueError("Missing status sections")
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown):
        url = urlsplit(link)
        if url.scheme or url.netloc or url.path.startswith("/"):
            if not link.startswith(PROJECT):
                raise ValueError(f"Use a link inside the project: {link}")
        else:
            target = ((ROOT / STATUS).parent / url.path).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                raise ValueError(f"Missing status evidence: {link}")
    with (ROOT / "hardware/revisions/assemblies.csv").open(encoding="utf-8-sig", newline="") as f:
        ids = [row["id"] for row in csv.DictReader(f)]
    for family in ("TW-A-0001-", "TW-A-0002-"):
        latest = max(item for item in ids if item.startswith(family))
        if latest not in markdown:
            raise ValueError(f"Update the handbook for registered assembly {latest}")


def compare_sources(base):
    changed = subprocess.check_output(["git", "diff", "--name-only", base + "...HEAD"], cwd=ROOT, text=True).splitlines()
    impact = [path for path in changed if SOURCES.fullmatch(path)]
    if impact and STATUS not in changed:
        raise ValueError("Review and update " + STATUS + " for changed records: " + ", ".join(impact))


def render_panel(snapshot):
    template = PANEL.read_text(encoding="utf-8").rstrip()
    if template.count(MARK) != 1 or template.count(ASSEMBLY_MARK) != 1:
        raise ValueError("Expected one placeholder each for the status snapshot and PCB assembly guide")
    assembly = base64.b64encode(ASSEMBLY.read_bytes()).decode("ascii")
    template = template.replace(ASSEMBLY_MARK, assembly)
    # An embedded document cannot close its containing script.
    payload = json.dumps(snapshot, ensure_ascii=True).replace("<", "\\u003c")
    return START + "\n" + template.replace(MARK, payload) + "\n" + END


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed", metavar="RELEASE_TAG", help="refresh the offline fallback for a packaged release")
    parser.add_argument("--base", help="check a PR's source changes against its merge base")
    args = parser.parse_args()
    record = (ROOT / STATUS).read_text(encoding="utf-8")
    validate_record(record)
    if args.base:
        compare_sources(args.base)
    # Preserve the archived handbook bytes around the status panel.
    book = BOOK.read_bytes().decode("utf-8")
    start = book.index(START)
    end = book.index(END, start) + len(END)
    if args.embed:
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", args.embed):
            raise ValueError("Use a release tag without URL or HTML syntax")
        rendered = render_panel({"tag": args.embed, "markdown": record})
        BOOK.write_bytes((book[:start] + rendered + book[end:]).encode("utf-8"))
    else:
        panel = book[start:end]
        snapshot = re.search(r'<script type="application/json" id="handbook-snapshot">(.+?)</script>', panel)
        if not snapshot or render_panel(json.loads(snapshot[1])) != panel:
            raise ValueError("Handbook reader differs from its source. Repackage with --embed RELEASE_TAG.")
    print("Verified live handbook reader, registered revisions and evidence links.")


if __name__ == "__main__":
    main()
