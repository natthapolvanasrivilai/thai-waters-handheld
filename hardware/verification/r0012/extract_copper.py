"""Run with KiCad 10's Python. Record copper length, width and conservative resistance."""
import hashlib
import json
import math
from pathlib import Path

import pcbnew as pcb

HERE = Path(__file__).resolve().parent
ELECTRICAL = HERE.parents[1] / "electronics"
BOARDS = {"A3": "pcb-haptic-cie-r0001/A3-CIE-R0001.kicad_pcb",
          "A4": "pcb-r0004/harness.kicad_pcb", "A5": "pcb-power-r0004/usb-input.kicad_pcb"}


def copper(source):
    board = pcb.LoadBoard(str(source))
    thickness = pcb.ToMM(board.GetDesignSettings().GetBoardThickness())
    by_net = {}
    # 25 um finished trace and 18 um via plating are proposed fabrication minima.
    # Sum every branch to upper-bound a path. This includes unused parallel branches.
    rho = 1.724e-5 * (1 + 0.00393 * (70 - 20))  # copper ohm.mm at 70 C
    for item in board.GetTracks():
        row = by_net.setdefault(item.GetNetname(), {"track_mm": 0, "vias": 0, "upper_ohm": 0})
        if isinstance(item, pcb.PCB_VIA):
            row["vias"] += 1
            drill = pcb.ToMM(item.GetDrillValue())
            row["upper_ohm"] += rho * thickness / (math.pi * drill * 0.018)
        else:
            length = pcb.ToMM(item.GetLength())
            row["track_mm"] += length
            row["upper_ohm"] += rho * length / (pcb.ToMM(item.GetWidth()) * 0.025)
    return {
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "board_thickness_mm": thickness,
        "nets": {name: {k:round(v, 7) for k,v in rec.items()} for name,rec in sorted(by_net.items())}
    }


if __name__ == "__main__":
    result = {label: copper(ELECTRICAL / path) for label,path in BOARDS.items()}
    (HERE / "copper.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
