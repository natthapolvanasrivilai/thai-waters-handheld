"""Mate the full supplier cable termination in both orientations, including all assembly displacement corners."""
import itertools,json
from pathlib import Path
import cadquery as cq
import sys
Q=Path(__file__).resolve().parent;R=Q.parent;H=R.parents[1]
sys.path.insert(0,str(R));import build
house=cq.Shape.importBrep(str(R/'CAD/housing-battery-bay.brep'))
source=cq.importers.importStep(str(H/'components/tensility-10-03675/10-03675.STEP')).val()
# Supplier C end points along -X. Rotate around (0,1,1) so long C profile axis
# coincides with installed Y and exposed C tip faces into the handheld along +X.
# 6.65 mm native projection minus maximum 6.40 mm engagement leaves 0.25 mm.
parts=source.Solids()
tip=cq.Compound.makeCompound([parts[0],parts[4],parts[5]]).rotate((0,0,0),(0,1,1),180)
record=[]
for angle in (0,180):
    plug=tip.rotate((0,0,0),(1,0,0),angle) if angle else tip
    for dx,dy,dz in [(0.,0.,0.),*itertools.product((-.15,.15),repeat=3)]:
        end=(-40.25+dx,dy,19.33+dz)
        closed=plug.translate(end)
        mask=build.shield_mask(offset=(dx,dy,dz))
        row=dict(orientation_deg=angle,socket_offset_mm=[dx,dy,dz],nominal_engagement_mm=6.4)
        # Distance to the exact finished part; subtract an allowance from the measured
        # gap for adverse extrusion rather than offsetting complex native STEP faces.
        row.update({name:round(closed.distance(s),5) for name,s in [('housing_clearance_mm',house),('tracked_mask_clearance_mm',mask)]})
        row['overlap_mm3']={name:round(closed.intersect(s).Volume(),7) for name,s in [('housing',house),('mask',mask)]}
        record.append(row);print(row,flush=True)
(Q/'tensility-fit.json').write_text(json.dumps(dict(source='Tensility 10-03675, MPN 50-00477 C plug, overmold 24-00113',supplier_assembly_solids=len(parts),supplier_shortened_cable_span_mm=150.,actual_purchased_cable_length_mm=1000.,
        print_allowance_each_side_mm=.10,positions=record),indent=2)+'\n')
