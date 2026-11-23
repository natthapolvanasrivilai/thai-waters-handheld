"""Build the three installed A5 leads on the display subassembly, in device millimetres."""
import argparse
import hashlib
import json
from pathlib import Path
from math import acos, tan

import cadquery as cq

HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / "usb-status-r0003/placed"
V = cq.Vector
COPPER = .127
JACKET = .260
TEE_STATION = 5.0
OPEN = (3.75, 6.25)


def sweep(edge, radius):
    wire = edge if isinstance(edge, cq.Wire) else cq.Wire.assembleEdges([edge])
    ring = cq.Wire.makeCircle(radius, wire.startPoint(), wire.tangentAt(0))
    return cq.Solid.sweep(ring, [], wire, isFrenet=True)


def cylinder(a, b, radius):
    v = b - a
    return cq.Solid.makeCylinder(radius, v.Length, a, v.normalized())


def curved(points):
    """Fillet each dressing point. Adjacent tangent setbacks fit the shared segment."""
    n = len(points)
    u = [(b-a).normalized() for a,b in zip(points, points[1:])]
    theta = [0] + [acos(max(-1., min(1., a.dot(b)))) for a,b in zip(u, u[1:])] + [0]
    t = [2.0 * tan(angle/2) for angle in theta]
    for i in range(n-1):
        length = (points[i+1] - points[i]).Length
        if t[i] + t[i+1] > .96*length:
            scale = .96*length / (t[i] + t[i+1])
            t[i] *= scale
            t[i+1] *= scale
    edges = []
    radii = []
    prev = points[0]
    for i in range(1, n-1):
        if theta[i] < 1e-4:
            continue
        v = points[i]
        a, b = v - u[i-1]*t[i], v + u[i]*t[i]
        radius = t[i]/tan(theta[i]/2)
        center = a + (u[i] - u[i-1]*u[i-1].dot(u[i])).normalized()*radius
        mid = center + ((a-center).normalized() + (b-center).normalized()).normalized()*radius
        edges.extend((cq.Edge.makeLine(prev, a), cq.Edge.makeThreePointArc(a, mid, b)))
        radii.append(radius)
        prev = b
    edges.append(cq.Edge.makeLine(prev, points[-1]))
    return cq.Wire.assembleEdges(edges), min(radii)


def form(cache):
    history = json.loads((OLD / "placement.json").read_bytes())
    lamp = cq.Edge.makeSpline([V(*p) for p in history["wire_control_points"]["USB-W4C"]])
    lamp_length = lamp.Length()
    def trim(a, b):
        return lamp.trim(lamp.paramAt(a / lamp_length), lamp.paramAt(b / lamp_length))
    tee = lamp.positionAt(TEE_STATION / lamp_length)
    seg = trim(*OPEN)
    tee_end = tee + V(1.4, 0, 0)
    common = sweep(lamp, COPPER)
    tails = cq.Shape.importBrep(str(cache / "USB-W4C-Cu.brep"))
    parts = {"USB-W4C-Cu": cq.Compound.makeCompound([common,*tails.Solids()])}
    lamp_sheath = [sweep(trim(a,b), JACKET).cut(common) for a,b in ((0,OPEN[0]),(OPEN[1],lamp_length))]
    parts["USB-W4C"] = cq.Compound.makeCompound(lamp_sheath)
    design = json.loads((HERE.parent/"design.json").read_bytes())
    locations = {r[0]: V(13+r[3],3+r[4],18.30) for r in design["parts"] if r[0] in ("W2","W3","W7")}
    # A5 plated holes take the stripped leads from the exposed, upward-facing back side.
    # Straight strain transitions at both ends are tangent to the curved jacket.
    points = {
        "W2": [locations["W2"],V(34.45,12,19.3),V(26,11.58,19.14),V(-17.35,18.5,18.0),
               V(-18.6,19.1,18.8),V(-19.06,19.82,20.18),V(-19.06,19.82,20.50)],
        "W3": [locations["W3"],V(34.45,5,19.3),V(26.34,8.86,19.14),V(3.56,10.56,18.46),
               V(-14.7,tee.y,tee.z),tee_end],
        "W7": [locations["W7"],V(30.65,17.3,19.22),V(29.4,17.3,19.22),V(15.46,19.06,19.48),
               V(-17.5,18.1,19.6),V(-19.98,18.47,20.0),V(-19.98,18.47,18.95)]
    }
    far = {"W2": V(-19.06,19.82,20.751), "W3": tee, "W7": V(-19.98,18.47,17.34)}
    lengths = {}
    for ref, vertices in points.items():
        lead, radius = curved(vertices)
        name = "A5-" + ref
        top = vertices[0]
        pin = V(top.x, top.y, 16.76 if ref == "W7" else 16.91)
        end = vertices[-1]
        core_edge = cq.Wire.assembleEdges([cq.Edge.makeLine(pin, top), *lead.Edges(),
                                           cq.Edge.makeLine(end, far[ref])])
        core = sweep(core_edge, COPPER)
        assert core.isValid()
        parts[name+"-Cu"] = core
        parts[name] = sweep(lead, JACKET).cut(core)
        # Ideal wetting envelopes on the upward A5 pad and J8 / resistor PCB land.
        # Exclude core volume from solder. The back of the native A5 copper is Z17.84.
        solder = cq.Solid.makeCone(.52,.16,.25,V(top.x,top.y,17.84)).cut(core)
        if ref == "W2":
            other = cq.Solid.makeCone(.16,.24,.19,V(-19.06,19.82,20.56)).cut(core)
        elif ref == "W7":
            solder = cq.Solid.makeCone(.52,.16,.25,V(top.x,top.y,17.05),V(0,0,-1)).cut(core)
            other = cq.Solid.makeCone(.33,.15,.20,V(-19.98,18.47,17.60),V(0,0,-1)).cut(core)
        else:
            # The single continuing J8-3 conductor is stripped locally. A soldered
            # side tap and its insulating overcoat occupy this short window.
            branch = cylinder(tee, tee_end, .18)
            other = sweep(seg,.205).fuse(branch).cut(common).cut(core)
            cover = sweep(seg,.39).fuse(cylinder(tee,tee_end,.36))
            parts["A5-W3-splice-cover"] = cover.cut(common).cut(core).cut(other)
        parts[name+"-solder"] = cq.Compound.makeCompound([solder,other])
        length = core_edge.Length()
        lengths[ref] = dict(conductor_length_mm=round(length,5), jacket_length_mm=round(lead.Length(),5),
                            min_centerline_bend_mm=round(radius,4), jacket_od_mm=2*JACKET,
                            a5_strip_mm=round((top-pin).Length,5), far_strip_mm=round((end-far[ref]).Length,5),
                            shared_J8_pigtail_mm=5.25 if ref=="W3" else 0,
                            wire_resistance_70C_ohm=round((length+(5.25 if ref=="W3" else 0))*1.724e-5*
                                                         (1+.00393*50)/(3.14159265359*COPPER**2),6),
                            dressing_points_mm=[[round(v,6) for v in p.toTuple()] for p in vertices])
    # Reserve working clearance for the W7 barrel and underside fillet when
    # dispensing the established resistor-carrier adhesive.
    original_bond = cq.Shape.importBrep(str(cache / "USB-BOND.brep"))
    keepout = cq.Solid.makeCylinder(.62,2.1,V(-19.98,18.47,16.7))
    parts["USB-BOND"] = original_bond.cut(keepout).clean()
    assert len(parts["USB-BOND"].Solids()) == 1
    return parts, lengths


def run(cache):
    parts, lengths = form(cache)
    rows = []
    for name, shape in parts.items():
        if not shape.isValid() or shape.Volume() <= 0:
            raise ValueError("Invalid " + name)
        target = HERE / (name + ".brep")
        shape.exportBrep(str(target))
        sha = hashlib.sha256(target.read_bytes()).hexdigest()
        color = "#b57547" if name.endswith("-Cu") else "#aba99c" if name.endswith("-solder") else (
            "#494b50" if "W3" in name or "W4C" in name else "#b9614e")
        rows.append(dict(name=name,brep=target.name,sha256=sha,label=name,group="Wiring",
                         ref="A5 / A1 / USB status",color=color,
                         note="Fixed display-subassembly lead. Nominal solder, pigtail and jacket fit require physical inspection."))
    (HERE/"installed.json").write_text(json.dumps(dict(remove=["USB-W4A","USB-W4A-Cu","USB-W4C","USB-W4C-Cu","USB-BOND"],
                                                    add=rows),indent=2)+"\n")
    (HERE/"routes.json").write_text(json.dumps(lengths,indent=2)+"\n")


if __name__ == "__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cache",type=Path,help="BRep cache from the registered R0011 reference assembly")
    run(cli.parse_args().cache)
