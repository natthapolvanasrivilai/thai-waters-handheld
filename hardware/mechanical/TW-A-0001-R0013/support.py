"""Model the installed insulating bond against the revised board's actual back copper."""
from pathlib import Path
import cadquery as cq
from assemble import HERE,ELECTRONICS,save,digest

if __name__=="__main__":
    boardfile=ELECTRONICS/"usb-entry-r0006/A5-power.brep"
    seatfile=ELECTRONICS/"harness-r0005/placed/A5-bond.brep"
    board=cq.Shape.importBrep(str(boardfile))
    bonds=cq.Shape.importBrep(str(seatfile))
    shapes=[]
    results=[]
    for pad in bonds.Solids():
        original=pad.Volume()
        installed=pad
        for feature in board.Solids():
            # Several KiCad STEP solids meet at the substrate plane. Only
            # positive-volume intrusions may displace a portion of adhesive.
            if feature.BoundingBox().zmax<=pad.BoundingBox().zmin+1e-6:
                continue
            cut=installed.intersect(feature)
            cutters=[piece for piece in cut.Solids() if piece.Volume()>1e-8]
            for cutter in cutters:
                installed=installed.cut(cutter)
            assert installed.isValid()
        overlap=original-installed.Volume()
        assert 0<=overlap<.04*3*3+.00001
        assert all(installed.intersect(s).Volume()<1e-6 for s in board.Solids()
                   if s.BoundingBox().zmax>pad.BoundingBox().zmin+1e-6)
        results.append({"center_mm":list(pad.Center().toTuple()),"copper_volume_in_original_bond_mm3":round(overlap,6)})
        shapes.append(installed)
    out=HERE/"A5-bond.brep"
    cq.Compound.makeCompound(shapes).exportBrep(str(out))
    save(HERE/"QA/A5-bond.json",{"A5_sha256":digest(boardfile),"original_bond_sha256":digest(seatfile),
         "fitted_bond_sha256":digest(out),"pad_results":results,
         "nominal_bond_mm":.25,"max_back_copper_over_plane_mm":round(board.BoundingBox().zmax-17.8,4),
         "scope":"Conformal insulating adhesive against the back-copper relief. Physical bond thickness, solder mask, cured adhesion and shock remain unmeasured."})
