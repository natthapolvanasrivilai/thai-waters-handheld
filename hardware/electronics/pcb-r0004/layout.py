"""Build the 23 x 13 mm harness board with the Python supplied by KiCad 10."""
import argparse
import csv
import uuid

from pathlib import Path

import pcbnew as pcb

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--footprints", type=Path, required=True, help="KiCad 10 standard footprint library directory")
args = parser.parse_args()

board = pcb.BOARD()
board.GetDesignSettings().SetBoardThickness(pcb.FromMM(0.8))
nets = {}
placements = {}
pin_position = {}
pin_net = {}
parts = []
harness = []


def point(xy):
    return pcb.VECTOR2I(*map(pcb.FromMM, xy))


def footprint(ref, value, lib, name, center, pins, rotation=0):
    lib_dir = HERE if lib == "TW" else args.footprints
    fp = pcb.FootprintLoad(str(lib_dir / (lib + ".pretty")), name)
    if not fp:
        raise ValueError(f"Missing {lib}:{name}")
    fp.SetFPID(pcb.LIB_ID(lib, name))
    symbol_id = uuid.uuid5(uuid.NAMESPACE_URL, "thai-waters/TW-A-0002-R0004/harness/" + ref)
    fp.SetPath(pcb.KIID_PATH("/" + str(symbol_id)))
    fp.SetSheetname("")
    fp.SetSheetfile("harness.kicad_sch")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(point(center))
    fp.SetOrientationDegrees(rotation)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    for i, net in enumerate(pins, 1):
        if net not in nets:
            nets[net] = pcb.NETINFO_ITEM(board, net)
            board.Add(nets[net])
        pad = fp.FindPadByNumber(str(i))
        pad.SetNet(nets[net])
        key = f"{ref}.{i}"
        p = pad.GetPosition()
        pin_position[key] = (pcb.ToMM(p.x), pcb.ToMM(p.y))
        pin_net[key] = net
    board.Add(fp)
    placements[ref] = center
    parts.append((ref, value, lib + ":" + name, *center, rotation))


def resistor(ref, value, package, center, pins):
    footprint(ref, value, "Resistor_SMD", package, center, pins)


def sot(ref, name, center, pins):
    footprint(ref, name, "Package_TO_SOT_SMD", "SOT-23", center, pins)


def terminal(i, net, center, angle, source):
    ref = f"J{i}"
    footprint(ref, net, "TW", "WireLand", center, [net], angle)
    harness.append((ref, net, *center, source))


# Top view in KiCad coordinates (X right, Y down), all dimensions in mm.
for i, (net, y, source) in enumerate([
    ("AMP_P", 1.6, "A1 J9-1 via retained keyed speaker plug, U6 OUT+ through R40"),
    ("SPK_P", 4.7, "SP1 Adafruit 3923 positive lead, identified by continuity/mark"),
    ("SPK_N", 8.3, "SP1 Adafruit 3923 negative lead"),
    ("AMP_N", 11.4, "A1 J9-2 via same keyed plug, U6 OUT- through R42"),
], 1):
    terminal(i, net, (1.6, y), 0, source)

for i, (net, x, source) in enumerate([
    ("SDA", 11.6, "A1 J8-27 ESP_SDA/GPIO8, fixed A1 end of W1"),
    ("VCC3V3", 14.1, "A1 J8-31 VCC3V3, fixed A1 end of W1"),
    ("SCL", 16.6, "A1 J8-25 ESP_SCL/GPIO7, fixed A1 end of W1"),
    ("USB_RAW", 19.1, "A1 J8-1 VBUS, retained raw tap if controller is revised"),
    ("VBAT", 21.6, "A1 J8-2 VBAT, protected J7 cell net"),
], 5):
    terminal(i, net, (x, 1.45), 90, source)

for i, (net, x, source) in enumerate([
    ("SW_SENSE", 11.6, "W3 remote SW1 white contact, disconnect prior direct K3 connection"),
    ("GND", 14.9, "W3 remote SW1 black contact"),
    ("GND", 18.2, "A1 original K3 pin 1 ground; verify to J8-3"),
    ("K3_RAW", 21.5, "A1 original K3 pin 2; continuity to R38 pad 2"),
], 10):
    terminal(i, net, (x, 11.55), 90, source)

small = "R_0603_1608Metric"
large = "R_2512_6332Metric"
resistor("R1", "4.99R", large, (6.55, 2.55), ["AMP_P", "SPK_P"])
resistor("R2", "4.99R", large, (6.55, 10.45), ["AMP_N", "SPK_N"])
resistor("R3", "1.50k", small, (12.65, 3.45), ["SDA", "VCC3V3"])
resistor("R4", "1.50k", small, (15.85, 3.45), ["VCC3V3", "SCL"])
resistor("R5", "330k", small, (11.9, 8.9), ["SW_SENSE", "KEY_AON"])
resistor("R6", "100k", small, (15.0, 9.2), ["N_GATE", "GND"])
sot("D1", "BAV170", (20.10, 4.4), ["USB_RAW", "VBAT", "KEY_AON"])
sot("Q1", "PMV65XP", (14.0, 6.35), ["SW_SENSE", "KEY_AON", "N_GATE"])
sot("Q2", "PMV16XN", (18.50, 8.30), ["N_GATE", "GND", "K3_RAW"])


def route(start, *steps, width=0.30, back=False):
    net = pin_net[start]
    a = pin_position[start]
    layer = pcb.B_Cu if back else pcb.F_Cu
    for step in steps:
        if step == "via":
            v = pcb.PCB_VIA(board)
            v.SetPosition(point(a))
            v.SetWidth(pcb.FromMM(0.70))
            v.SetDrill(pcb.FromMM(0.30))
            v.SetNet(nets[net])
            board.Add(v)
            layer = pcb.B_Cu if layer == pcb.F_Cu else pcb.F_Cu
            continue
        if isinstance(step, str):
            if pin_net[step] != net:
                raise ValueError((start, step))
            b = pin_position[step]
        else:
            b = step
        t = pcb.PCB_TRACK(board)
        t.SetLayer(layer)
        t.SetStart(point(a))
        t.SetEnd(point(b))
        t.SetWidth(pcb.FromMM(width))
        t.SetNet(nets[net])
        board.Add(t)
        a = b


route("J1.1", (2.60, 1.60), "R1.1", width=0.80)
route("R1.2", (9.5125, 3.8), (8.2625, 5.05), (2.60, 5.05), "J2.1", width=0.80)
route("R2.2", (9.5125, 9.2), (8.2625, 7.95), (2.60, 7.95), "J3.1", width=0.80)
route("J4.1", (2.60, 11.40), "R2.1", width=0.80)
route("J5.1", (11.6, 3.225), "R3.1")
route("J6.1", (14.1, 2.825), "R3.2")
route("R3.2", "R4.1")
route("J7.1", (16.6, 3.375), "R4.2")
route("J8.1", (19.1, 3.3875), "D1.1")
route("J9.1", (21.6, 2.6), (22.20, 3.2), (22.20, 5.70),
      (21.65, 6.25), (20.0625, 6.25), "D1.2")
route("D1.3", (21.0375, 3.35), "via", (17.50, 3.35),
      (13.0625, 7.7875), (13.0625, 8.20), "via", "Q1.2")
route("R5.2", (13.0625, 8.5625), (13.0625, 8.20))
route("Q1.1", (12.6, 5.4), (11.075, 6.925), "R5.1")
route("R5.1", (11.075, 11.225), "J10.1")
route("Q1.3", (14.9375, 7.50), (14.175, 8.2625), "R6.1")
route("Q1.3", (15.5, 6.35), (16.5, 7.35), "Q2.1")
route("R6.2", (16.5, 9.875), (16.5, 10.0),
      (16.8125, 10.0), "Q2.2")
route("J11.1", (14.9, 11.60), (16.5, 10.0))
route("J12.1", (18.2, 9.8875), "Q2.2")
route("Q2.3", (20.0, 8.30), (21.5, 9.80), "J13.1")


def edge(a, b):
    sh = pcb.PCB_SHAPE(board)
    sh.SetShape(pcb.SHAPE_T_SEGMENT)
    sh.SetLayer(pcb.Edge_Cuts)
    sh.SetStart(point(a))
    sh.SetEnd(point(b))
    sh.SetWidth(pcb.FromMM(0.05))
    board.Add(sh)


corners = [(0, 0), (23, 0), (23, 13), (0, 13)]
for a, b in zip(corners, corners[1:] + corners[:1]):
    edge(a, b)


def label(value, center, layer, size=0.8):
    t = pcb.PCB_TEXT(board)
    t.SetText(value)
    t.SetPosition(point(center))
    t.SetLayer(layer)
    t.SetMirrored(layer == pcb.B_SilkS)
    t.SetTextSize(point((size, size)))
    t.SetTextThickness(pcb.FromMM(0.15))
    board.Add(t)


label("TW R0004", (6.2, 6.5), pcb.F_SilkS)
for ref, net, x, y, _ in harness:
    label(ref, (x + 0.3 if x < 2 else x, y if x < 2 else (y + 0.2 if y < 2 else y - 0.2)), pcb.B_SilkS)
label("HARNESS", (6.5, 5.5), pcb.B_SilkS)
label("R0004", (6.5, 7.3), pcb.B_SilkS)

pcb.SaveBoard(str(HERE / "harness.kicad_pcb"), board)
for filename, header, rows in [
    ("placement.csv", ["ref", "value", "footprint", "x_mm", "y_mm", "rot_deg"], parts),
    ("harness.csv", ["ref", "net", "x_mm", "y_mm", "endpoint"], harness),
    ("netlist.csv", ["net", "component.pad"], sorted((net, key) for key, net in pin_net.items())),
]:
    with (HERE / filename).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)

