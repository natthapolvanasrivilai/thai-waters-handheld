"""Certify that the final rigid USB1 pose is trapped in the legacy pocket.

Run using project CAD Python and Numba. Translation and Euler angles provide
continuous local coordinates around the seat; all angles are far from the
Euler singularity. An interval test covers every boundary face of a 6-D box
containing the seat. In each boundary cell some material box from the PCB
intersects verified housing stock throughout the entire cell. Therefore every
continuous rigid path from outside that box to the seat must cross solid stock.
"""
import json

import numba as nb
import numpy as np


ORIGIN = np.array([-41.8, 0.,13.1])
# All boxes lie strictly inside the checked solid. The lamp is unnecessary.
STOCK = [
    [[-44,-3.6,14.151],[-42.201,3.6,15.445]],
    [[-41.389,-3.6,14.151],[-40.2,3.6,15.445]],
    [[-42.201,-3.6,14.151],[-41.389,-2.521,15.445]],
    [[-42.201,2.521,14.151],[-41.389,3.6,15.445]],
    [[-42.20,-2.52,15.391],[-41.39,2.52,15.445]],
    [[-43.249,-2.919,10.821],[-41.251,2.919,11.389]],
]
for side in [-1,1]:
    for x1,x2,y in [(-43.249,-42.201,2.361),(-42.201,-41.389,2.521),(-41.389,-41.251,2.361)]:
        y1,y2 = sorted([side*y,side*2.949])
        STOCK.append([[x1,y1,11.321],[x2,y2,14.869]])
MATERIAL = [[[-.299,-2.399,-1.599],[.299,2.399,-.21]],
            [[-.299,-2.399,.21],[.299,2.399,1.599]]]
for y1,y2 in [(-2.399,-1.91),(-1.49,1.49),(1.91,2.399)]:
    MATERIAL.append([[-.299,y1,-.211],[.299,y2,.211]])
MATERIAL = np.array(MATERIAL)
STOCK = np.array(STOCK) - ORIGIN


@nb.njit
def certificate(p, half, stock, material):
    """Robust separating-axis overlap. Return positive if every pose collides."""
    ax,ay,az = p[3:]
    sx,sy,sz = np.sin(ax),np.sin(ay),np.sin(az)
    cx,cy,cz = np.cos(ax),np.cos(ay),np.cos(az)
    r = np.array([[cy*cz,sx*sy*cz-cx*sz,cx*sy*cz+sx*sz],
                  [cy*sz,sx*sy*sz+cx*cz,cx*sy*sz-sx*cz],
                  [-sy,sx*cy,cx*cy]])
    # Fifteen separating axes for two boxes. Use unit axes for distances.
    axes = np.zeros((15,3))
    axes[:3,:] = np.eye(3)
    axes[3:6,:] = r.T
    for i in range(3):
        for j in range(3):
            t = np.cross(axes[i],axes[3+j])
            length = np.sqrt((t*t).sum())
            if length > 0.:
                axes[6+3*i+j] = t/length
    # For each housing/PCB box pair, its configuration obstacle with frozen
    # rotation is a convex Minkowski sum. These SAT axes are its facet normals.
    # Testing every facet places the full translation uncertainty box AND a
    # ball of radius 2.91 * sum(angle halfwidths) inside that obstacle.
    # Perturbing rotation can move any PCB point by at most that radius and
    # thus reduce its support in any direction by at most the same amount.
    err = np.abs(axes) @ half[:3] + 2.91 * half[3:].sum() + 1.e-8
    ac = ((stock[:,0,:]+stock[:,1,:])/2) @ axes.T
    ar = ((stock[:,1,:]-stock[:,0,:])/2) @ np.abs(axes).T
    bc = (((material[:,0,:]+material[:,1,:])/2) @ r.T + p[:3]) @ axes.T
    br = ((material[:,1,:]-material[:,0,:])/2) @ np.abs(axes@r).T
    best = -1.e6
    for i in range(len(stock)):
        for j in range(len(material)):
            margin = 1.e6
            for k in range(15):
                if np.all(axes[k] == 0):
                    continue
                value = ar[i,k]+br[j,k]-abs(ac[i,k]-bc[j,k])-err[k]
                if value < best:
                    margin = value
                    break
                margin = min(margin,value)
            best=max(best,margin)
            if best>0:
                return best
    return best


def main():
    import cadquery as cq
    from check_motion import BASE, MECH, HERE, ROOT, box, volume, part, gauge, components, record, read
    sources = {}
    containment = {}
    def native_box(bounds):
        lo,hi = bounds
        return cq.Solid.makeBox(*(hi-lo), cq.Vector(*lo))
    for rev in [BASE,MECH / "TW-A-0001-R0014", MECH / "TW-A-0001-R0015"]:
        housing = part(rev,"housing-battery-bay",sources)
        row = read(rev / "part-orientations.json")["housing-battery-bay"]
        native = cq.Shape.importBrep(str(record(rev / row["assembly_brep"], sources)))
        containment[rev.name + " print"] = max(volume(box(*b) - housing) for b in STOCK + ORIGIN)
        containment[rev.name + " native"] = max(abs(native_box(b).cut(native).Volume()) for b in STOCK + ORIGIN)
    boards = {"USB1 gauge":gauge("USB-PCB1",sources),
              "USB1 real PCB mesh":components(sources,HERE.parents[1])["USB-PCB1"]}
    for key,board in boards.items():
        containment[key] = max(volume(box(*b) - board) for b in MATERIAL + ORIGIN)
    native_pcb = cq.Shape.importBrep(str(record(
        ROOT / "hardware/electronics/usb-status-r0003/placed/USB-PCB1.brep", sources)))
    containment["USB1 real PCB native"] = max(abs(native_box(b).cut(native_pcb).Volume())
                                                for b in MATERIAL + ORIGIN)
    assert max(containment.values()) < 1e-9, containment
    radius = np.linalg.norm(np.max(np.abs(MATERIAL),axis=(0,1)))
    assert radius < 2.91
    domain = np.array([[-.5,.5],[-.4,.4],[-.4,.85],[-10,10],[-12,12],[-8,8]],float)
    declared_domain = domain.tolist()
    domain[3:] *= np.pi/180
    counts = []
    for i in range(6):
        for side in (0,1):
            row = domain.copy()
            row[i,:] = domain[i,side]
            stack = [(row.mean(axis=1), np.diff(row).ravel()/2)]
            count = 0
            certified_cells = 0
            smallest_reserve = np.inf
            while stack:
                p,h = stack.pop()
                count += 1
                reserve = certificate(p,h,STOCK,MATERIAL)
                if reserve > 0:
                    certified_cells += 1
                    smallest_reserve = min(smallest_reserve,reserve)
                    continue
                weight = h * [1,1,1,2.91,2.91,2.91]
                k = int(np.argmax(weight))
                if weight[k] < .0001:
                    raise RuntimeError(f"Unverified boundary cell on axis {i}, side {side}: {p}, {h}")
                h = h.copy()
                h[k] /= 2
                step = np.zeros(6)
                step[k] = h[k]
                stack.extend([(p-step,h),(p+step,h)])
            counts.append(dict(coordinate=["X","Y","Z","Rx","Ry","Rz"][i],
                               bound=declared_domain[i][side], visited_cells=count, certified_leaves=certified_cells,
                               minimum_certified_reserve_after_numeric_buffer_mm=round(smallest_reserve,10)))
    data = dict(assemblies=["TW-A-0001-R0013","TW-A-0001-R0014","TW-A-0001-R0015"],
                result="All 12 faces of a closed 6-D region around the seat are obstructed. A continuous rigid placement from above the rim to the registered seat cannot exist.",
                frame="Offsets from the installed PCB centre; rotation Rz @ Ry @ Rx. Translation in mm, angles in degrees.",
                rotation_origin_xyz_mm=ORIGIN.tolist(), domain_xyz_rxryrz=declared_domain,
                method="Interval separating-axis intersection of one PCB material box and one housing material box per leaf. The separating-axis margins include the entire translation interval, the full rotation displacement bound and a 1e-8 mm numerical buffer. Every bounding face is covered.",
                max_material_radius_mm=round(radius,7), rotation_bound_radius_mm=2.91,
                housing_stock_boxes_installed_mm=np.round(STOCK+ORIGIN,4).tolist(),
                pcb_material_boxes_installed_mm=np.round(MATERIAL+ORIGIN,4).tolist(),
                max_box_outside_each_source_mm3=containment,
                boundary_faces=counts, sources_sha256=sources,
                scope="Nominal rigid housing and board without deformation, machining or destruction. The proof needs no other parts or wiring. R0013 inherits the R0011 print housing.")
    (HERE / "legacy-trap.json").write_bytes((json.dumps(data,indent=2)+"\n").encode())
    print("12 boundary faces certified",flush=True)


if __name__ == "__main__":
    main()
