"""Build the offline handbook's revision lookup from the same CSVs used on the traveler."""
import csv
from html import escape
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent


def rows(name):
    with (HERE / f"{name}.csv").open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def add_register(page, repo_url):
    def link(path, label):
        href = repo_url + "/blob/main/" + quote(path, safe="/")
        return f'<a href="{escape(href, quote=True)}">{escape(label)}</a>'

    parts = {row["id"]: row for row in rows("parts")}
    members = rows("members")
    panels = []
    for assembly in rows("assemblies"):
        identifier = assembly["id"]
        label = " · ".join(filter(None, [identifier, assembly["legacy_alias"], assembly["name"]]))
        items = []
        for entry in (r for r in members if r["assembly"] == identifier):
            p = parts[entry["part"]]
            source_name = entry["member"] or Path(entry["source"]).name
            items.append("<tr><td>" + escape(p["id"]) + "</td><td>" + escape(p["name"])
                         + "</td><td>" + escape(entry["quantity"]) + "</td><td>"
                         + link(entry["source"], source_name) + "</td></tr>")
        panels.append("<details><summary>" + escape(label) + "</summary><div><p>"
                      + escape(assembly["description"]) + " · " + link(assembly["evidence"], "Design evidence")
                      + '</p><div class="gridtable"><table><thead><tr><th>Part revision</th><th>Part</th>'
                      + "<th>Qty</th><th>Source or ZIP member</th></tr></thead><tbody>"
                      + "".join(items) + "</tbody></table></div></div></details>")
    section = ('<section id="revisions" hidden><h2>Hardware revisions</h2>'
               '<p>Open an assembly to find exact part revisions and source files. '
               'The next inert fit print uses TW-A-0001-R0008 and the TW-A-0002-R0002 electrical package. '
               'Record firmware version and digest separately.</p>'
               + "<p>" + link("hardware/revisions/README.md", "Allocation, verification and serial traceability")
               + "</p>" + "".join(panels) + "</section>")
    changes = [
        ("</main>", section + "</main>"),
        ("assembly:'3D assembly',", "assembly:'3D assembly',revisions:'Hardware revisions',"),
        ("['circuits','Review circuit evidence'", "['revisions','Find a hardware revision',"
         "'Match historical assembly labels to exact part revisions and source files.','Hardware-and-3D.md'],"
         "['circuits','Review circuit evidence'"),
    ]
    for old, new in changes:
        if page.count(old) != 1:
            raise ValueError(f"Handbook revision navigation anchor changed: {old}")
        page = page.replace(old, new)
    return page
