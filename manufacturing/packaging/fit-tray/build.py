"""Size a hand-cut inert packout trial from the installed component register (mm)."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ROD = {"Removable rod grip", "Grip lock screw", "Grip screw keeper"}
# Finished clear inside dimensions after assembly, including the divider caliper.
CARTON = (222, 142, 52)
BOARD = 1.5
WALL = 48
FOOT = 8
LONG_DIVIDER_Y = 88
SHORT_DIVIDER_X = 119
KEY_DIVIDER_X = 143
PARTITIONS = {
    "handheld": (0, 0, SHORT_DIVIDER_X, LONG_DIVIDER_Y),
    "USB cable": (SHORT_DIVIDER_X + BOARD, 0, CARTON[0], LONG_DIVIDER_Y),
    "detached grip": (0, LONG_DIVIDER_Y + BOARD, KEY_DIVIDER_X, CARTON[1]),
    "sleeved key": (KEY_DIVIDER_X + BOARD, LONG_DIVIDER_Y + BOARD, CARTON[0], CARTON[1]),
}


def extent(components, members):
    return [round(max(components[n]["bounds_mm"][axis + 1] for n in members)
                  - min(components[n]["bounds_mm"][axis] for n in members), 3)
            for axis in (0, 2, 4)]


def sheet(elements):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" '
            'viewBox="0 0 297 210"><style>text{font:3.4px sans-serif;fill:#222}'
            'rect,path{fill:none;stroke:#222;stroke-width:0.32}.score{stroke:#26738c;'
            'stroke-dasharray:2 1}.bay{stroke:#999;stroke-dasharray:1 1}</style>\n'
            + "\n".join(elements) + '\n</svg>\n')


def label(x, y, text):
    return f'<text x="{x}" y="{y}">{text}</text>'


def calibration():
    return ['<path d="M15 190v4m0 -2h50m0 -2v4"/>', label(15, 199, "50 mm scale check")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=ROOT / "hardware/mechanical/TW-A-0001-R0011/installed-step.json")
    args = parser.parse_args()
    components = json.loads(args.model.read_text())["components"]
    body = extent(components, set(components) - ROD)
    grip = extent(components, ROD)
    samples = {"handheld": body, "detached grip": [grip[1], grip[0], grip[2]]}
    records = {}
    layout = [label(15, 10, "PK2 / inert packout proof / 1:1 / floor layout, milled or hand-cut dummy stock"),
              '<g transform="translate(15,18)">', f'<rect width="{CARTON[0]}" height="{CARTON[1]}"/>']
    for name, (x0, y0, x1, y1) in PARTITIONS.items():
        # Worst floor buildup is one carton-board foot. Both dividers face away from the junction.
        bay = [x1-x0, y1-y0, CARTON[2]-BOARD]
        item = samples.get(name)
        surplus = [round(b-a, 3) for a,b in zip(item, bay)] if item else None
        if surplus is not None and min(surplus) <= 0:
            raise ValueError(f"{name} exceeds bay: {surplus}")
        records[name] = dict(clear_bay_mm=bay, item_envelope_mm=item, total_free_space_mm=surplus)
        layout += [f'<rect x="{x0}" y="{y0}" width="{bay[0]}" height="{bay[1]}" class="bay"/>',
                   label(x0+3,y0+8,name), label(x0+3,y0+14,f"{bay[0]} x {bay[1]} mm")]
        if item:
            layout.append(f'<rect x="{x0+surplus[0]/2}" y="{y0+surplus[1]/2}" width="{item[0]}" height="{item[1]}" class="score"/>')
    layout += ['</g>', label(15,168,"Dashed envelopes show nominal CAD. Cable coil and tool sleeve need physical measurements."),
               *calibration()]
    dieline = [label(15,9,"PK2 / cut three separate dividers. Solid = cut. Dashed = score. Glue each foot to the carton floor.")]
    for x,y,length,name in [(15,15,CARTON[0]-1,"A / across full width"),
                            (15,82,LONG_DIVIDER_Y-0.5,"B / front to A"),
                            (115,82,CARTON[1]-LONG_DIVIDER_Y-BOARD-0.5,"C / rear to A")]:
        dieline += [f'<rect x="{x}" y="{y}" width="{length}" height="{WALL+FOOT}"/>',
                    f'<path class="score" d="M{x} {y+WALL}h{length}"/>',
                    label(x+3,y+9,name),label(x+3,y+15,f"{length} x {WALL+FOOT} mm")]
    dieline += [label(15,152,"Score 8 mm from the foot. Form 90 degrees. Set the finished inside faces to the floor drawing."),
                label(15,160,"A foot faces the grip. B foot faces the cable. C foot faces the key. Trim the foot only at junctions."),
                *calibration()]
    (HERE/"floor-layout.svg").write_text(sheet(layout), encoding="utf-8")
    (HERE/"divider-dieline.svg").write_text(sheet(dieline), encoding="utf-8")
    data = {"source":args.model.resolve().relative_to(ROOT).as_posix(), "component_count":len(components),
            "carton_finished_inside_mm":CARTON, "wall_stock_assumed_mm":BOARD, "bays":records,
            "status":"inert dimensional trial; physical samples, restraint, and transport qualification pending"}
    (HERE/"dimensions.json").write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
