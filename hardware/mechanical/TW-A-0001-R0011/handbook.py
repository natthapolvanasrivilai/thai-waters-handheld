"""Embed controlled hardware evidence in the standalone handbook, preserving released game bytes."""
import base64
import csv
import gzip
import html
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ELECTRICAL = ROOT / "hardware/electronics/integration-r0004"
BOOK = ROOT / "docs/index.html"
MODEL = ROOT / "docs/models/TW-A-0001-R0011-exploded.html"
GH = "https://github.com/natthapolvanasrivilai/thai-waters-handheld"
page = BOOK.read_text(encoding="utf8")


def replace_payload(source, name, content):
    pattern = rf'(<script id="{name}"[^>]*>)[^<]*(</script>)'
    updated, matches = re.subn(pattern, lambda match: match[1] + content + match[2], source)
    if matches != 1:
        raise ValueError(name)
    return updated


def info_link(path, title):
    return f'<a href="{GH}/{path}">{html.escape(title)}</a>'


def table_row(row):
    cells = [row[k] for k in ("case", "metric", "value", "unit", "lo", "hi", "status")]
    return "<tr>" + "".join("<td>" + html.escape(value or "—") + "</td>" for value in cells) + "</tr>"


def recovery_plot():
    # Preserve the local extrema of every bucket when decimating solver output.
    with zipfile.ZipFile(ELECTRICAL / "solver-evidence.zip") as archive:
        log = archive.read("candidate/recovery_nocell_low.log").decode("ascii", errors="replace")
    columns = []
    samples = []
    for line in log.splitlines():
        fields = line.split()
        if fields[:2] == ["Index", "time"]:
            columns = fields
        elif fields and fields[0].isdigit() and "v(obs)" in columns and "v(pmic)" in columns and len(fields) == len(columns):
            samples.append((float(fields[1])*1000, float(fields[columns.index("v(obs)")])*1000, float(fields[columns.index("v(pmic)")])))
    if len(samples) < 100 or samples[-1][0] < 13.9:
        raise ValueError("Missing recovery trace")
    pieces = []
    for channel, name, maximum, unit in ((1, "Host current", 300, "mA"), (2, "PMIC input", 5.5, "V")):
        reduced = []
        for start in range(0, len(samples), 32):
            block = samples[start:start+32]
            reduced += sorted({block[0], min(block, key=lambda v:v[channel]), max(block, key=lambda v:v[channel]), block[-1]})
        coords = " ".join(f"{40+x[0]*38:.2f},{128-x[channel]*105/maximum:.2f}" for x in reduced)
        pieces.append(f'<figure><figcaption>{name} ({unit})</figcaption><svg role="img" aria-label="{name} during USB configuration and revocation, over 14 milliseconds" viewBox="0 0 600 155" style="width:100%;max-width:670px;background:#fff;color:#233e37"><path d="M40 23V128H572" fill="none" stroke="currentColor"/><polyline points="{coords}" fill="none" stroke="#13755a" stroke-width="2"/><g fill="currentColor" font-size="12"><text x="2" y="26">{maximum}</text><text x="22" y="130">0</text><text x="39" y="147">0 ms</text><text x="294" y="147">7 ms</text><text x="545" y="147">14 ms</text></g></svg></figure>')
    return '<details><summary>Inspect the simulated USB recovery waveform</summary><p>Low-input battery-absent case at 4.75 V source. The host configures the recovery bridge, then revokes the grant. Each trace follows the same 14 ms window.</p>'+''.join(pieces)+'</details>'


with (ELECTRICAL / "results.csv").open(encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))
verification = json.loads((ELECTRICAL / "verification.json").read_text())
if len({r["case"] for r in rows}) != verification["candidate_cases"]:
    raise ValueError("Case count disagrees with the engine report")
bench = info_link("issues/12", "First-article measurements")
tracker = info_link("issues/1", "Hardware and playtest tracker")
print_kit = info_link("releases/tag/r0011-receiver-toolpaths-2", "Receiver-down fit-print kit")
sources = info_link("tree/main/hardware/electronics/integration-r0004", "Circuit designs, solver evidence and limitations")
details = f"""<article><h2>R0004 circuit verification</h2>
<p>{verification['candidate_cases']} ngspice cases. Each row shows a modeled value and its acceptance bounds in the stated unit. The record includes deliberate fault injections and unresolved operating conditions. The original circuit studies follow below.</p>
<p>{sources} · {bench}</p>
{recovery_plot()}
<label>Filter results <input type="search" id="gateSearch" placeholder="Circuit, measurement or limit"></label>
<label>Disposition <select id="gateStatus"><option>All</option><option>OUTSIDE</option><option>WITHIN</option><option>RECORD</option></select></label>
<output id="gateCount" aria-live="polite"></output>
<div style="overflow:auto;max-height:30rem"><table><thead><tr><th>Case</th><th>Metric</th><th>Value</th><th>Unit</th><th>Minimum</th><th>Maximum</th><th>Disposition</th></tr></thead>
<tbody id="gateRows">{''.join(map(table_row, rows))}</tbody></table></div></article>"""
model_bytes = MODEL.read_bytes()
page = replace_payload(page, "compressedModel", base64.b64encode(gzip.compress(model_bytes, mtime=0)).decode())
page = page.replace("R0009 engineering assembly", "R0011 engineering assembly")
page = page.replace("R0009 dressed mechanical assembly viewer", "R0011 engineering inspection viewer")
page = page.replace("R0009 design review · R0003 electrical", "R0011 fit print · R0004 electrical review")
page = page.replace("R0009 / R0003 is the current engineering review. R0008 / R0002 remains the released inert-fit baseline.", "R0011 is the current inert fit print. R0004 circuit changes are under engineering review.")
section = f"""<script id="hardware-gate-review">
(() => {{
 const assembly = document.querySelector('#assembly h2');
 assembly.insertAdjacentHTML('afterend', {json.dumps(f'<p>{print_kit} · {tracker} · {bench}</p>')});
 document.getElementById('business').insertAdjacentHTML('afterbegin',{json.dumps('<p><strong>Historical cost baseline.</strong> The searchable R0009 BOM below predates the R0011 print and the R0004 circuit proposals. The R0010 covered-housing model budgeted $112.06 in allocated materials and $146.65 assembled. For budgeting, substituting the R0011 housing and factory-terminated leads yields $123.45 in allocated materials before controller changes, the FR-4 spacer, identification and rework. The R0004 fitted electronics still need a complete procurement quote.</p>')});
 document.getElementById('circuits').insertAdjacentHTML('afterbegin', {json.dumps(details)});
 const q=document.getElementById('gateSearch'), status=document.getElementById('gateStatus');
 const rows=Array.from(document.querySelectorAll('#gateRows tr'));
 function update() {{
   const term=q.value.trim().toLowerCase();
   let n=0;
   for (const row of rows) {{
     row.hidden=!(row.textContent.toLowerCase().includes(term) && (status.value==='All' || row.lastElementChild.textContent===status.value));
     if(!row.hidden) n++;
   }}
   document.getElementById('gateCount').textContent=n+' of '+rows.length+' measurements';
 }}
 q.addEventListener('input',update);
 status.addEventListener('change',update);
 update();
}})();
</script>"""
page = re.sub(r'<script id="hardware-gate-review">.*?</script>\s*', "", page, flags=re.S)
page = page.replace("</html>", section + "\n</html>")
BOOK.write_bytes(page.encode("utf8"))
