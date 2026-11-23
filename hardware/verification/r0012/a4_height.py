"""Re-run the rigid rocker/board portion of the A4 mounting-height trade study."""
from pathlib import Path
import sys
import cadquery as cq
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/"hardware/mechanical/TW-A-0001-R0012"))
from service_check import tri, model, meshgap, HARNESS
from mate import split_latch, actuate, STROKE

def placed(name):
    return cq.Shape.importBrep(str(HARNESS/"placed"/(name+".brep")))

rocker = actuate(split_latch(placed("A3-J1-plug"))[1], 1)
board = placed("A4-integration")
old_seat = board.translate((0,0,-1.0))
print(f"Original seat. Pressed rocker interference {old_seat.intersect(rocker).Volume():.5f} mm^3")
moving = model(*tri(rocker))
fixed = model(*tri(old_seat))
print("Lift / lowest sampled rocker clearance / withdrawal (mm)")
for height in (0.8,0.95,1.0,1.05,1.2):
    fixed.setTranslation(np.array([0.,0.,height]))
    gaps=[]
    for travel in np.linspace(0.,STROKE,67):
        moving.setTranslation(np.array([0.,travel,0.]))
        gaps.append((meshgap(moving,fixed),travel))
    gap,travel=min(gaps)
    print(f"{height:.3f} / {gap:.5f} / {travel:.3f}")
