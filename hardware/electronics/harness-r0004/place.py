"""Build the R0004 A3 connector and four separately terminated power/bus leads."""
import hashlib
import json
from pathlib import Path
import cadquery as cq

HERE = Path(__file__).resolve().parent
OUT = HERE / "placed"
OLD = HERE.parent / "haptic-r0009/placed"
ORIGIN = (0, 0, 0)
PIN_Y = {1: -1.08, 2: -3.62, 3: -6.16, 4: -8.70, 5: -11.24}
PIN_Z = 10.31
FRONT = 17.92
PLUG_END = FRONT + 12.85
# Each tap is on the straight section of the W1 wire approaching the encoder.
ROWS = [(1,"VCC",21.80,12.85,9.10),(3,"SCL",20.05,9.61,12.28),
        (4,"SDA",22.8,10.69,11.22),(5,"GND",24.75,11.77,10.16)]
V = cq.Vector
parts = {}
routes = {}


def add(name, shape, label, color, note):
    assert shape.isValid() and shape.Volume() > 0, name
    parts[name] = (shape, label, color, note)


def box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, V(x, y, z))


def cylinder(a, b, radius):
    start, end = V(*a), V(*b)
    axis = end - start
    return cq.Solid.makeCylinder(radius, axis.Length, start, axis.normalized())


def wire(points, radius, tangents=None):
    edge = cq.Edge.makeSpline([V(*p) for p in points],
            tangents=[V(*t) for t in tangents] if tangents else None)
    profile = cq.Wire.makeCircle(radius, edge.startPoint(), edge.tangentAt(0))
    return cq.Solid.sweep(profile, [], edge, True, False), edge.Length()


def board_point(x, y, z):
    # Rotate the 20 mm square A3 counterclockwise about its centre, preserving the pad area.
    return (20.8 - (y+6.0), -6.8 + (x-21.0), z)


def orient(shape):
    return shape.rotate((21,-6,0), (21,-6,1), 90).translate((-.2,-.8,0))


def main():
    board_parts = cq.Shape.importBrep(str(OLD / "drvParts.brep")).Solids()
    assert len(board_parts) == 17 and board_parts[0].BoundingBox().zmax > 14
    add("drvParts", cq.Compound.makeCompound(board_parts[1:]), "A3 populated components",
        "#393d39", "Boardoza manufacturer geometry after removal of the supplied straight strip.")
    add("drvBoard",cq.Shape.importBrep(str(OLD/"drvBoard.brep")),"A3 Boardoza PCB",
        "#257a42","Original R1.0 PCB, turned 90 degrees counterclockwise on the support pads.")
    hdr = cq.importers.importStep(str(HERE / "source-cad/61900519521.step")).val()
    hdr = hdr.rotate(ORIGIN, (0, 0, 1), -90).translate((12.90, -1.08, 7.11))
    add("A3-J1-header", hdr, "A3 J1 top-lock angled header", "#ddd6ba",
        "Würth 61900519521 manufacturer STEP. Pin 1 is nearest -X. Socket withdraws toward +Y.")
    shim = box(11.55, -12.70, 6.11, 6.15, 13.10, 1.00)
    for y in PIN_Y.values():
        shim = shim.cut(cylinder((12.9,y,6), (12.9,y,7.3), .60))
    add("A3-J1-spacer", shim, "J1 1 mm FR-4 spacer", "#9a9c69",
        "Unclad drilled FR-4 separates the plug and onboard components. Five 1.20 mm holes.")

    # Catalog envelope. The inserted nose, terminal windows and latch relief are
    # local section estimates, independently identified in the parts manifest.
    house = box(FRONT,-12.77,7.52,12.85,13.22,4.05)
    house = house.fuse(box(FRONT+8.24,-12.77,11.57,4.61,13.22,2.15))
    for y in PIN_Y.values():
        house = house.cut(box(FRONT-.01,y-.92,8.98,12.87,1.84,2.28))
        house = house.cut(box(FRONT+5.3,y-.60,7.50,2.10,1.20,1.50))
    add("A3-J1-plug", house.clean(), "J1 five-way female housing", "#f3eace",
        "61900511621 drawing-based fit study. Cavity 2 is vacant and encloses its pin.")

    for pin, net, tee_x, tee_y, tee_z in ROWS:
        y = PIN_Y[pin]
        # A formed terminal study uses the 9.50 mm loose-contact overall and
        # 0.20 mm strip thickness. The compliance geometry requires a sample.
        nose = FRONT+2.90
        x = nose + 4.30
        spring = box(nose,y-.70,PIN_Z-.53,4.50,1.40,.20)
        for side in (-1,1):
            spring = spring.fuse(box(nose,y+(.50 if side==1 else -.70),PIN_Z-.53,4.50,.20,1.06))
        spring = spring.fuse(box(nose+3.4,y-.6,PIN_Z-.53,2.2,1.20,.2))
        crimp = cylinder((x,y,PIN_Z),(nose+7.2,y,PIN_Z),.49).cut(
            cylinder((x-.01,y,PIN_Z),(nose+7.21,y,PIN_Z),.203))
        sleeve = cylinder((nose+7.15,y,PIN_Z),(nose+9.5,y,PIN_Z),.88).cut(
            cylinder((nose+7.14,y,PIN_Z),(nose+9.51,y,PIN_Z),.75))
        crimp = crimp.fuse(box(nose+6.8,y-.14,PIN_Z-.82,.9,.28,.6))
        contact = spring.fuse(crimp,sleeve).clean()
        add(f"A3-J1-C{pin}", contact, f"J1 position {pin} {net} socket", "#b2a49e",
            "Stamped terminal and closed crimp study on a factory lead. Spring geometry is approximate.")
        stripped = cylinder((nose+4.85,y,PIN_Z),(nose+7.18,y,PIN_Z),.203)
        add("wh"+net+"-Cu", stripped, f"{net} core inside crimp", "#b26c43",
            "26 AWG copper conductor in the conductor barrel.")
        # Form the lead away from the housing before the bend back to its W1 tee.
        # Vertical separation where the branches turn prevents conductor crossings.
        x, rear, _ = board_point(PLUG_END,y,PIN_Z)
        start = V(*board_point(nose+7.18,y,PIN_Z))
        exit_point = V(x,rear+.25,PIN_Z)
        branch_dx = {1:1.00,3:-.28,4:-.12,5:-.25}[pin]
        end = V(tee_x-branch_dx,tee_y-1.35,tee_z-.30)
        arm = V(branch_dx,1.35,.30).normalized()
        # The jacket stays straight through the barrel and the housing. A cubic
        # guide sets the exit tangent and follows the inclination of the tee.
        start_reach = {1:4.3,3:2.15,4:2.5,5:3.6}[pin]
        end_reach = {1:3.5,3:2.2,4:2.5,5:2.6}[pin]
        bend = cq.Edge.makeBezier([exit_point,exit_point+V(0,start_reach,0),end-arm*end_reach,end])
        straight=cq.Edge.makeLine(start,exit_point)
        path=cq.Wire.assembleEdges([straight,bend])
        profile=cq.Wire.makeCircle(.75,start,V(0,1,0))
        insulation=cq.Solid.sweep(profile,[],path,True,False)
        length=path.Length()
        points=[p.toTuple() for p in [start,exit_point,exit_point+V(0,start_reach,0),end-arm*end_reach,end]]
        min_radius=1/max(bend.curvatureAt(i/100) for i in range(101))
        add("wh"+net, insulation, f"W4 {net} factory lead", "#373b3f",
            "Würth 619100126015 black 26 AWG pigtail. Identify by numbered cavity and continuity.")
        routes[net] = dict(cavity=pin, control_points_mm=points, minimum_centerline_bend_radius_mm=round(min_radius,3), modeled_jacket_diameter_mm=1.5,
                           jacket_length_mm=round(length,3),source_stock_mm=150)

    # Copper only reaches the solder land of J1-2 and J1-5. The insulated
    # midsection lies below the PCB and outboard of both intervening pin tails.
    points=[(13.68,-3.62,3.96),(14.76,-4.70,3.96),
            (14.76,-10.16,3.96),(13.68,-11.24,3.96)]
    a,b,c,d=[V(*p) for p in points]
    first=cq.Edge.makeThreePointArc(a,V(14.443675,-3.936325,3.96),b)
    last=cq.Edge.makeThreePointArc(c,V(14.443675,-10.923675,3.96),d)
    curve=cq.Wire.assembleEdges([first,cq.Edge.makeLine(b,c),last])
    strap=cq.Solid.sweep(cq.Wire.makeCircle(.4,a,first.tangentAt(0)),[],curve,True,False)
    add("A3-mode-strap",strap,"Underside insulated trigger strap","#42494d",
        "30 AWG insulated link J1-2 to J1-5. Test with plug removed.")
    tails = [cylinder(p,(12.9,p[1],3.96),.127) for p in [points[0],points[-1]]]
    add("A3-mode-strap-Cu",cq.Compound.makeCompound(tails),"Trigger strap solder ends","#b26c43",
        "Bond each exposed end only to its own header tail underneath A3.")
    for k, (shape,label,color,note) in list(parts.items()):
        if not (k.startswith("wh") and not k.endswith("-Cu")):
            parts[k] = (orient(shape),label,color,note)
    # Motor's two factory stubs stay fixed. Re-form the trimmed leads to the
    # rotated original TP1/TP2 locations clear of the A3 plug and body.
    for k,pin_y,stub_x,lanex in [("wm0",-7.90,19.475,32.6),("wm1",-2.40,18.507,34.0)]:
        pad=board_point(29.10,pin_y,6.55)
        q=[(stub_x,9.0,6.04),(stub_x,7.7,6.04),
           (pad[0],5.4,6.40),pad]
        formed,length=wire(q,.275,[(0,-1,0),(0,-1,-.3)])
        add(k,formed,"Motor factory lead "+k[-1],"#a34747" if k=="wm0" else "#3d4244",
            "Continuous 0.55 mm SparkFun factory motor lead to its original TP on the rotated A3.")
        add(k+"-Cu",cylinder(pad,(pad[0],pad[1],5.50),.127),"Motor pad solder end","#b26c43",
            "Original output-pad termination carried into the new A3 position.")
        routes[k]=dict(points_mm=q, jacket_length_mm=round(length,3))
    # Move each solder tap along its original continuous straight W1 trunk.
    # The original stripped window is closed in the cable solid first.
    tee_remove = []
    previous = HERE.parent / "harness-r0003/placed"
    for pin,net,tee_x,tee_y,z in ROWS:
        old_y = {"VCC":1.2,"GND":3.4,"SDA":5.8,"SCL":7.8}[net]
        name="w1"+net
        old_wire = cq.Shape.importBrep(str(previous/(name+".brep")))
        restore = cylinder((30,old_y-1.42,z),(30,old_y+1.42,z),.4)
        trunk = old_wire.fuse(restore).clean()
        trunk = trunk.cut(box(tee_x-1.4,tee_y-.6,z-.6,2.8,1.2,1.2))
        add(name,trunk,"W1 "+net+" trunk","#834735" if net=="VCC" else "#54565a",
            "Original 30 AWG route, with stripped window at the relocated haptic tee.")
        a=(tee_x-{1:1.00,3:-.28,4:-.12,5:-.25}[pin],tee_y-1.35,z-.30)
        b=(tee_x,tee_y,z)
        arm=V(*b)-V(*a)
        copper=cylinder((tee_x-1.4,tee_y,z),(tee_x+1.4,tee_y,z),.127).fuse(cylinder(a,b,.203))
        seal=cylinder((tee_x-1.4,tee_y,z),(tee_x+1.4,tee_y,z),.43).fuse(
             cq.Solid.makeCone(.75,.34,arm.Length,V(*a),arm.normalized()))
        for suffix,shape,col in [("-Cu",copper,"#b26c43"),("-seal",seal.cut(copper),"#515450")]:
            key="tee-"+net+suffix
            add(key,shape,key,col,"Individually insulated W1 solder tap to the trimmed 26 AWG W4 lead.")
            tee_remove.append(key)
        tee_remove.append(name)
    manifest = {"remove":["drvParts","drvBoard","wm0","wm1","wm0-Cu" ,"wm1-Cu"]+tee_remove+["wh"+n+s for n in ("VCC","GND","SDA","SCL","Trig") for s in ("","-Cu")], "add":[]}
    OUT.mkdir(exist_ok=True)
    for name,(shape,label,color,note) in parts.items():
        p = OUT / (name+".brep")
        shape.exportBrep(str(p))
        manifest["add"].append(dict(name=name,brep="placed/"+p.name,label=label,
                                     group="Haptics",ref="A3 J1",color=color,note=note,
                                     sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    (HERE/"installed.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (HERE/"routing.json").write_text(json.dumps(routes,indent=2)+"\n")


if __name__ == "__main__":
    main()
