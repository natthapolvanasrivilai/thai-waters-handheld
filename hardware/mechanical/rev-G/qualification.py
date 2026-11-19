"""Check continuous open-shell gauge insertion, local wall sections and closed-unit gaps."""
import cadquery as cq
from geometry import CX,CY,Z,box

def run(shapes):
    shell=shapes['Housing']
    def gap(a,b):return round(a.distance(b),4)
    def overlap(a,b):return round(max(0.,a.intersect(b).Volume()),5)
    def corridor(s):
        # Conservative union of each component's projected bounding prism, extending
        # past the front of the open housing throughout the full vertical insertion.
        paths=[]
        for solid in s.Solids():
            b=solid.BoundingBox()
            paths.append(box(b.xmin,b.ymin,b.zmin,b.xlen,b.ylen,40-b.zmin))
        return paths[0].fuse(*paths[1:]).clean() if len(paths)>1 else paths[0]
    checks={};gaps={}
    for case in ('Cell','cellDrawing','cellAlt'):
        pack=shapes[case];path=corridor(pack)
        checks[case]={k:overlap(path,shapes[k]) for k in ('Housing','Retainer','Keeper screw','Key PCB','Speaker','drvBoard','motor','Receiver nut keeper')}
        gaps[case]={k:gap(pack,shapes[k]) for k in ('Housing','bridge','ph','packplug','batt0','batt1','shrink0','shrink1','Speaker','drvBoard')}
    # Margin for the drawing maximum and alternative PCM/body above nominal seating.
    # Leads have a separate tunnel and are evaluated with their actual geometry.
    guard=box(CX-19.0,CY-31.55,Z-.4,38,63.1,7.2)
    guard_hits={k:overlap(guard,shapes[k]) for k in ('Housing','ph','packplug','shrink0','shrink1')}
    # The bridge is above the cell body, but the battery grows at the PCM end;
    # the bridge crosses a different Y station. Record both actual envelope gaps.
    wall={}
    for name,start,end in [('lead tunnel end wall',(CX,35,10),(CX,42,10)),('lead tunnel roof',(CX,35.4,13.7),(CX,35.4,20)),('lead tunnel floor',(CX,35.4,0),(CX,35.4,8)),('tray floor',(CX,0,-6),(CX,0,3)),('south wall at cell base',(CX,-36,3.6),(CX,-31.8,3.6))]:
        edge=cq.Edge.makeLine(cq.Vector(*start),cq.Vector(*end))
        wall[name]=round(sum(e.Length() for e in shell.intersect(edge).Edges()),4)
    stroke=[]
    for i in range(15):
        key=shapes['Key cap'].translate((0,-i*.05,0))
        stroke.append(dict(travel_mm=round(i*.05,2),housing_mm3=overlap(key,shell),keeper_mm3=overlap(key,shapes['Retainer'])))
    offsets=[]
    for pack_id in ('cellDrawing','cellAlt'):
        for dx in (-.25,.25):
            for dy in (-.25,.25):
                for dz in (0,.30):
                    sample=shapes[pack_id].translate((dx,dy,dz))
                    offsets.append(dict(pack=pack_id,offset_mm=[dx,dy,dz],shell_mm3=overlap(sample,shell),bridge_mm3=overlap(sample,shapes['bridge'])))
    wires={}
    for case,names in [('catalog',['pack0','pack1']),('alt',['altTail0','altTail1']),('drawing',['drawingTail0','drawingTail1'])]:
        leads=[shapes[k] for k in names];adapters=[shapes['batt0'],shapes['batt1']]
        wires[case]=dict(factory_pair_mm=gap(*leads),adapter_pair_mm=gap(*adapters),
                         adapter_to_factory_mm=min(gap(a,b) for a in adapters for b in leads),
                         factory_to_shell_mm=min(gap(a,shell) for a in leads))
    return dict(wire_separation_mm=wires,key_stroke=stroke,rigid_placement_corners=offsets,insertion_sweep_overlap_mm3=checks,seated_distance_mm=gaps,clearance_box_intersections_mm3=guard_hits,wall_section_mm=wall)

