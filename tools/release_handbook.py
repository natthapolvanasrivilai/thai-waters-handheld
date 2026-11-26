"""Deterministically render an offline snapshot from the exact Git source."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re
import subprocess

TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


def git_bytes(root, *args):
    return subprocess.check_output(("git", "-C", str(root), *args))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def render(root, doc):
    h = doc["handbook"]
    edition = h["edition"]
    prefix = {"owner-private": "docs/wiki/", "public": "docs/release-handbook-public/"}[edition]
    source = doc["source_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", source):
        raise ValueError("Use an exact 40-character source SHA")
    tracked = git_bytes(root, "ls-tree", "-r", "--name-only", "-z", source, "--", prefix)
    names = sorted(p for p in tracked.decode().split("\0") if p.endswith(".md"))
    if prefix + "Home.md" not in names:
        raise ValueError("No approved handbook edition Home.md in exact release source")
    content = {}
    for p in names:
        meta = git_bytes(root, "ls-tree", source, "--", p).split()
        if not meta or meta[0] != b"100644" or meta[1] != b"blob":
            raise ValueError(f"Handbook content must be a regular Markdown file: {p}")
        content[p] = git_bytes(root, "show", f"{source}:{p}")
        if not content[p].strip():
            raise ValueError(f"Empty handbook source: {p}")
    if edition == "public":
        # No fallback, symlinks, exact copies of private chapters or literal links
        # into the private edition. A human still reviews public content.
        private = git_bytes(root, "ls-tree", "-r", "--name-only", "-z", source,
                            "--", "docs/wiki/").decode().split("\0")
        sensitive = {digest(git_bytes(root, "show", f"{source}:{p}"))
                     for p in private if p.endswith(".md")}
        for p, data in content.items():
            if digest(data) in sensitive or re.search(
                    rb"(?:docs/wiki/|\.\./wiki/|github\.com/[^)\s]*/wiki/)", data, re.I):
                raise ValueError(f"Public handbook contains a private-edition source or link: {p}")
    status = {k: doc["checks"][k]["status"] for k in sorted(doc["checks"])}
    record = dict(schema=1, edition=edition, stage=doc["stage"], release_version=h["release_version"],
                  release_tag=h["release_tag"], revision=doc["revision"], source_commit=source,
                  hardware_revision=h["hardware_revision"], firmware_revision=h["firmware_revision"],
                  software_revision=h["software_revision"],
                  changes=h["changes"], revision_na=h.get("revision_na", {}), evidence_status=status,
                  source_documents={p: digest(data) for p, data in content.items()})
    payload = json.dumps(record, ensure_ascii=True, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e")
    labels = [("Version", h["release_version"]), ("Release tag", h["release_tag"]),
              ("Product revision", doc["revision"]), ("Hardware", h["hardware_revision"]),
              ("Firmware", h["firmware_revision"]), ("Software", h["software_revision"]), ("Source commit", source),
              ("Distribution edition", edition), ("Release stage", doc["stage"])]
    esc = lambda s: escape(s, quote=True)
    reason = {"Hardware": "hardware_revision", "Firmware": "firmware_revision",
              "Software": "software_revision"}
    header = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}" +
                     (f" — {esc(h.get('revision_na', {}).get(reason[k], ''))}"
                      if v == "none" and k in reason else "") + "</dd>" for k,v in labels)
    changes = "".join(f"<li>{esc(item)}</li>" for item in h["changes"])
    status_rows = "".join(f"<tr><th scope='row'>{esc(k)}</th><td>{esc(v)}</td></tr>" for k,v in status.items())
    names = sorted(names, key=lambda p: (not p.endswith("/Home.md"), p))
    links, sections = [], []
    for i,p in enumerate(names):
        title = Path(p).stem.replace("-", " ")
        links.append(f'<li><a href="#doc-{i}">{esc(title)}</a></li>')
        blocks = []
        for line in content[p].decode().splitlines():
            m = re.match(r"^(#{1,4})\s+(.+)$", line)
            if m:
                level = min(len(m[1])+2, 6)
                blocks.append(f"<h{level}>{esc(m[2])}</h{level}>")
            elif line:
                blocks.append(f'<div class="source">{esc(line)}</div>')
            else:
                blocks.append("<p></p>")
        sections.append(f'<article id="doc-{i}"><h2>{esc(title)}</h2>{"".join(blocks)}</article>')
    return f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pocket Reel release handbook · {esc(h["release_version"])}</title>
<style>
body{{font:16px/1.58 system-ui,sans-serif;background:#f8f8f7;color:#151716;max-width:76ch;margin:auto;padding:1.25rem}}
h1,h2,h3{{line-height:1.24}} dl{{display:grid;grid-template-columns:10em minmax(0,1fr);gap:.3em}}
dd{{margin:0;overflow-wrap:anywhere}} article{{border-top:1px solid #bbb;margin-top:1.75rem;padding-top:1rem}}
table{{border-collapse:collapse}} td,th{{padding:.3rem .7rem;border:1px solid #bbb;text-align:left;overflow-wrap:anywhere}}
.source{{white-space:pre-wrap;overflow-wrap:anywhere}}
@media(max-width:36em){{dl{{display:block}} dd{{margin-bottom:.6em}}}}
</style>
<main>
<h1>Pocket Reel release handbook</h1><p>Standalone offline edition. All included source text is embedded below. Source Markdown links to other assets are reference text, not offline dependencies.</p>
<dl>{header}</dl>
<h2>Changes in this revision</h2><ul>{changes}</ul>
<h2>Release evidence status</h2><table><thead><tr><th>Check</th><th>Status</th></tr></thead><tbody>{status_rows}</tbody></table>
<nav aria-label="Handbook sections"><h2>Handbook sections</h2><ul>{"".join(links)}</ul></nav>
{"".join(sections)}
</main><script id="release-handbook-metadata" type="application/json">{payload}</script></html>
'''.encode("utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("manifest", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    data = render(a.root, json.loads(a.manifest.read_text(encoding="utf-8")))
    a.output.write_bytes(data)
    print(digest(data), a.output.name)


if __name__ == "__main__":
    main()
