"""Roll up the dressed R0009 prototype BOM using the released slice and wire routes."""
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CAD = ROOT / "hardware/mechanical/TW-A-0001-R0009"
ELECTRONICS = ROOT / "hardware/electronics"
BOM = HERE / "R0009-buy-make-bom.csv"
D = Decimal


def rounded(value, places=2):
    return value.quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)


def write_csv(path, rows):
    with path.open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def group(ref, printed):
    if printed:
        return "Printed parts"
    if ref in {"A1", "B1", "A2", "MG1"}:
        return "Controller, battery, reel sensor and magnet"
    if ref == "SD1":
        return "Full artwork microSD"
    if ref in {"A3", "M1", "SP1", "SP1-G", "C7"}:
        return "Audio and rumble"
    if ref.startswith("H"):
        return "Fasteners and handle hardware"
    if ref.startswith("PK") or ref == "USB1":
        return "Pack and USB cable"
    return "Wiring, switches, indicators and consumables"


def validate_local(link):
    name, _, anchor = link.partition("#")
    path = ROOT / name
    if not path.is_file() or not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Missing drawing {link}")
    if anchor:
        headings = re.findall(r"^#+ (.+)$", path.read_text(encoding="utf8"), re.M)
        if anchor not in {heading.lower().replace(" ", "-") for heading in headings}:
            raise ValueError(f"Missing section {link}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


with BOM.open(encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))
slices = json.loads((CAD / "QA/print-audit.json").read_text())
trunk = json.loads((ELECTRONICS / "harness-r0003/placed/w1.json").read_text())["wires"]
branch = json.loads((ELECTRONICS / "haptic-r0009/placed/routes.json").read_text())
cut_mm = {}
for i, net in enumerate(("VCC", "GND", "SDA", "SCL"), 1):
    cut_mm[f"W1-{i}"] = trunk[net]["finished_path_mm"] + 5
    route = branch["wh" + net]
    tip_mm = math.dist(route["points_mm"][-1], route["stripped_tail_end_mm"])
    cut_mm[f"W4-{i}"] = route["insulated_length_mm"] + tip_mm + 5
cut_mm["W4-5"] = branch["whTrig"]["insulated_length_mm"] + 2 * 1.02 + 5

totals = defaultdict(Decimal)
variants = defaultdict(Decimal)
details, evidence = [], []
seen, printed = set(), set()
seconds = 0
grams = D(0)
for row in rows:
    ref = row["Ref"]
    mpn = row["MPN or process"]
    if ref in seen:
        raise ValueError(f"Duplicate reference {ref}")
    seen.add(ref)
    if ref in cut_mm:
        row["Qty per unit"] = str(math.ceil(cut_mm[ref]) / 1000)
        row["Disposition"] = "Cut allocation includes 5 mm handling allowance above the dressed conductor path including stripped ends, rounded up to whole mm. Trim to fit."
    qty = D(row["Qty per unit"])
    if qty < 0 or (qty == 0) != (ref == "BT2"):
        raise ValueError(f"Invalid prototype quantity {ref}")
    if mpn in slices:
        if qty != 1 or mpn in printed:
            raise ValueError(f"Unexpected printed part quantity for {mpn}")
        printed.add(mpn)
        piece = slices[mpn]
        weight = D(str(piece["total_g"]))
        rate = D(".045") if mpn == "usb-c-shield-mask" else D(".025")
        material = "two opaque TPU 95A colours" if mpn == "usb-c-shield-mask" else "transparent PETG" if mpn.startswith("status-") else "opaque PETG"
        row["USD at 1"] = str(weight * rate)
        row["Price basis"] = f"{weight} g {material} × USD {rate * 1000}/kg on single-material slice, includes slice support and brim. Two-colour TPU changeover excluded."
        grams += weight
        seconds += sum(int(n) * {"h": 3600, "m": 60, "s": 1}[unit] for n, unit in re.findall(r"(\d+)([hms])", piece["estimated_time"]))
    price = D(row["USD at 1"]) if qty else None
    cost = qty * price if qty else D(0)
    category = group(ref, mpn in slices)
    totals[category] += cost
    variants[row["Variant"]] += cost
    url = row["Source URL or drawing"]
    spec = row["Specification or route"]
    file_hash = "" if url.startswith("https://") else validate_local(url)
    spec_hash = validate_local(spec) if spec and not spec.startswith("https://") else ""
    if not row["Evidence ID"] or not url:
        raise ValueError(f"Missing source {ref}")
    evidence.append(dict(ref=ref,source_type=row["Source type"],identifier=row["Evidence ID"],source=url,
                         source_sha256=file_hash,specification=spec,specification_sha256=spec_hash,
                         basis=row["Price basis"],review="2026-11-19"))
    details.append(dict(Ref=ref,group=category,Variant=row["Variant"],Description=row["Description"],mpn=mpn,
                        qty=qty,UOM=row["UOM"],price=price if price is not None else "",ext=rounded(cost,6),
                        Source=row["Source"],url=url,basis=row["Price basis"]))
if len(printed) != 16 or len(set(slices) - printed) != 2:
    raise ValueError("Expected 16 installed prints and two excluded battery gauges")

write_csv(BOM, rows)
write_csv(HERE / "R0009-prototype-budget.csv", details)
write_csv(HERE / "R0009-source-evidence.csv", evidence)
materials = sum(totals.values())
hours = D(seconds) / D(3600)
labor = D("2.5") * 12
machine = hours * D(".75")
power = hours * D(".12") * D(".14")
conversion = labor + machine + power
usd = lambda value: float(rounded(value))
summary = dict(
    groups_usd={k: usd(v) for k, v in totals.items()},
    variant_materials_usd={k: usd(v) for k, v in variants.items()},
    line_count=len(rows), positive_quantity_lines=len(rows)-1,
    installed_prints=len(printed), printed_grams=float(grams), sliced_hours=float(rounded(hours,3)),
    materials_usd=usd(materials), conversion_usd=usd(conversion), assembled_usd=usd(materials+conversion),
    built_in_only_materials_usd=usd(materials-variants["Full artwork"]),
    built_in_only_assembled_usd=usd(materials+conversion-variants["Full artwork"]),
    cash_low_usd=usd(materials+40),cash_high_usd=usd(materials+115),
    cash_basis="Illustrative stocked-workshop allocation with USD 25–70 in extra pack/setup charges and USD 15–45 in freight. Excludes tax and labor. This is not an empty-shelf purchase quote.",
    empty_shelf_checkout_usd=None,
    empty_shelf_example="Just the selected Kester spool ($263.31), 3M 4991 roll ($179.24), DOWSIL tube ($75.88) and two Jonard spools ($24.86 each) total $568.15 before shipment or any other line. Converter, PCB and remaining checkout totals require quotes.",
    conversion_basis={"assembly_hours":2.5,"labor_usd_per_hour":12,"printer_usd_per_hour":0.75,
                      "average_printer_kW":0.12,"energy_usd_per_kWh":0.14,
                      "labor_usd":usd(labor),"printer_usd":usd(machine),"energy_usd":usd(power)},
    scope="One dressed, packaged prototype with rumble, handle, full artwork card and cable. Excludes RTC backup cell, shop gauges, two-colour purge and setup, tax, freight, yield and production qualification. Totals use unrounded extensions."
)
(HERE / "R0009-budget.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n",encoding="utf8")
print(json.dumps(summary,indent=2,ensure_ascii=True))
