"""Allocate and inspect Thai Waters hardware identifiers. Uses the Python standard library."""
import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TABLES = {
    "assemblies": "id,legacy_alias,name,description,evidence,changes",
    "parts": "id,name,source,member,sha256",
    "members": "assembly,part,quantity,source,member",
}
ID = re.compile(r"(TW-([AP])-(\d{4,}))-R(\d{4,})")
SERIES = re.compile(r"TW-[AP]-\d{4,}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_table(name, content):
    reader = csv.DictReader(io.StringIO(content))
    require(reader.fieldnames == TABLES[name].split(","), f"{name}: unexpected columns")
    rows = list(reader)
    require(all(None not in row and None not in row.values() for row in rows), f"{name}: malformed row")
    return rows


def index(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), f"duplicate {key}")
    return result


def local_path(name):
    require(name and PurePosixPath(name).as_posix() == name and "\\" not in name
            and not Path(name).is_absolute() and ".." not in PurePosixPath(name).parts,
            f"expected a repository-relative path: {name}")
    path = (ROOT / name).resolve()
    require(name and path.is_relative_to(ROOT) and path.is_file(), f"missing source: {name}")
    return path


@lru_cache(maxsize=None)
def digest(name, member):
    path = local_path(name)
    if member:
        with ZipFile(path) as archive:
            data = archive.read(member)
    else:
        data = path.read_bytes()
    if (member or name).lower().endswith(".md"):
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def check_baseline(tables, ref):
    """Published rows and complete membership of a published assembly are immutable."""
    relative = HERE.relative_to(ROOT).as_posix()
    prior = {}
    for name in TABLES:
        source = f"{ref}:{relative}/{name}.csv"
        content = subprocess.check_output(["git", "show", source], cwd=ROOT).decode("utf-8")
        prior[name] = read_table(name, content)
        current = {tuple(row.values()) for row in tables[name]}
        require(all(tuple(row.values()) in current for row in prior[name]), f"{name}: changed or removed a row from {ref}")
    old_ids = {row["id"] for row in prior["assemblies"]}
    existing = [row for row in tables["members"] if row["assembly"] in old_ids]
    require(len(existing) == len(prior["members"]), f"membership of a baseline in {ref} changed")
    for name in ("parts", "assemblies"):
        old_keys = {r["id"] for r in prior[name]}
        highest = {}
        for key in old_keys:
            family, suffix = key.rsplit("-R", 1)
            highest[family] = max(highest.get(family, 0), int(suffix))
        for key in {r["id"] for r in tables[name]} - old_keys:
            family, suffix = key.rsplit("-R", 1)
            require(int(suffix) > highest.get(family, 0), f"{key}: revision precedes a published baseline")


def validate(tables, against):
    parts = index(tables["parts"], "id")
    assemblies = index(tables["assemblies"], "id")
    for kind, records in [("P", parts), ("A", assemblies)]:
        for key, row in records.items():
            m = ID.fullmatch(key)
            require(m and m[2] == kind, f"invalid identifier: {key}")
            number, revision = int(m[3]), int(m[4])
            require(number and revision and key == f"TW-{kind}-{number:04}-R{revision:04}", f"invalid number: {key}")
            require(row["name"].strip(), f"{key}: missing name")
    aliases = [r["legacy_alias"].casefold() for r in assemblies.values() if r["legacy_alias"]]
    require(len(set(aliases)) == len(aliases), "duplicate legacy alias")
    with (ROOT / "quality/changes.csv").open(encoding="utf-8-sig", newline="") as f:
        changes = {r["Change"] for r in csv.DictReader(f)}
    for row in assemblies.values():
        local_path(row["evidence"])
        require(all(k in changes for k in row["changes"].split("|") if k), f"{row['id']}: unknown change")
    for key, row in parts.items():
        require(digest(row["source"], row["member"]) == row["sha256"], f"{key}: definition digest mismatch")
    slots = set()
    used = set()
    for row in tables["members"]:
        a, p = row["assembly"], row["part"]
        require(a in assemblies and p in parts, f"unknown assembly or part: {a} {p}")
        require(re.fullmatch(r"[1-9]\d*", row["quantity"]), f"{a} {p}: invalid quantity")
        slot = (a, p)
        require(slot not in slots, f"{a}: duplicate part revision {p}")
        slots.add(slot)
        used.add(p)
        require(digest(row["source"], row["member"]) == parts[p]["sha256"], f"{a} {p}: supplied bytes differ")
    require(set(assemblies) == {a for a, _ in slots}, "assembly without members")
    require(set(parts) == used, "part without an assembly")
    # Cross-check the archived engineering result independently from the new registers.
    manifest = json.loads((ROOT / "hardware/mechanical/rev-G/print-manifest.json").read_text())
    g = {Path(r["source"]).stem: parts[r["part"]]["sha256"] for r in tables["members"] if r["assembly"] == "TW-A-0001-R0007"}
    require(g == {k: v["sha256"] for k, v in manifest.items()}, "Rev G print manifest differs")
    if against:
        check_baseline(tables, against)
    print(f"Verified {len(assemblies)} assembly baselines, {len(parts)} part revisions and {len(slots)} memberships.")


def next_id(tables, request):
    ids = [r["id"] for t in ("parts", "assemblies") for r in tables[t]]
    if request.lower() in ("part", "assembly"):
        kind = "P" if request.lower() == "part" else "A"
        numbers = [int(m[3]) for key in ids if (m := ID.fullmatch(key)) and m[2] == kind]
        return f"TW-{kind}-{max(numbers, default=0)+1:04}-R0001"
    series = request.upper()
    require(SERIES.fullmatch(series), "use part, assembly, or a family such as TW-A-0001")
    revisions = [int(m[4]) for key in ids if (m := ID.fullmatch(key)) and m[1] == series]
    require(revisions, f"unknown family: {series}")
    return f"{series}-R{max(revisions)+1:04}"


def show(tables, query):
    parts = index(tables["parts"], "id")
    assemblies = index(tables["assemblies"], "id")
    aliases = {r["legacy_alias"].casefold(): r["id"] for r in assemblies.values() if r["legacy_alias"]}
    label = ("Rev " + query if len(query) == 1 else query).casefold()
    key = aliases.get(label, query.upper())
    require(key in assemblies or key in parts, f"unknown revision or alias: {query}")
    row = (assemblies if key in assemblies else parts)[key]
    print(f"{key}  {row['name']}  {row.get('legacy_alias', '')}")
    if key in assemblies:
        print(row["description"], row["evidence"], sep="\n")
    else:
        print("SHA-256", row["sha256"])
    for entry in tables["members"]:
        a, p = entry["assembly"], entry["part"]
        if key in (a, p):
            source = entry["source"] + ("!" + entry["member"] if entry["member"] else "")
            print(f"  {a}  {entry['quantity']} x {p}  {parts[p]['name']}  {source}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True, dest="command")
    commands.add_parser("check").add_argument("--against", metavar="GIT_REF", help="compare with an earlier registered commit")
    commands.add_parser("next").add_argument("family", help="part, assembly, or an existing family such as TW-P-0001")
    commands.add_parser("show").add_argument("query", help="a full assembly ID, part revision or historical alias")
    args = parser.parse_args()
    try:
        tables = {n: read_table(n, (HERE / (n + ".csv")).read_text(encoding="utf-8-sig")) for n in TABLES}
        if args.command == "check":
            validate(tables, args.against)
        elif args.command == "next":
            print(next_id(tables, args.family))
        else:
            show(tables, args.query)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as e:
        parser.exit(1, f"{e}\n")


if __name__ == "__main__":
    main()
