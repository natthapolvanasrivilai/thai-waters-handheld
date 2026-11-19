"""Measure the seven circular horizontal bore stations and their as-modelled roof profiles."""
import json
import math

import cadquery as cq

from build import HERE, V

FEATURES=[
    ("housing-battery-bay","Power cap guide",(-36,34.05,12.5),(0,1,0),(1,0,1),3.0),
    ("housing-battery-bay","Cap flange counterbore",(-36,33.20,12.5),(0,1,0),(1,0,1),4.15),
    ("rod-grip","M3 through-bore",(17,-24.5,-2),(0,0,1),(0,-1,0),1.78),
    ("rod-grip","Captive head chamber",(17,-24.5,-8),(0,0,1),(0,-1,0),3.12),
    ("rod-grip","Keeper counterbore",(17,-24.5,-14.1),(0,0,1),(0,-1,0),4.63),
    ("PKCELL-max-body-with-wire-sockets","Left inert lead socket",(-1.45,28.5,2.65),(0,1,0),(0,0,1),.80),
    ("PKCELL-max-body-with-wire-sockets","Right inert lead socket",(1.45,28.5,2.65),(0,1,0),(0,0,1),.80),
]


def main():
    results=[]
    for name,feature,center,axis,up,r in FEATURES:
        s=cq.Shape.importBrep(str(HERE/"CAD"/(name+".brep")))
        c=V(*center)
        u=V(*up).normalized()
        side=V(*axis).cross(u).normalized()
        checks={}
        # The upper two roof facets are tangent to the circular arc at 45 degrees.
        # Probe the diagonal facet normals, the apex and three working directions.
        for theta in (-22.5,0.,22.5,45.,90.,180.,270.):
            a=math.radians(theta)
            d=u*math.cos(a)+side*math.sin(a)
            ray=cq.Edge.makeLine(c,c+d*(r*2.6))
            distances=[(p.Center()-c).dot(d) for p in s.intersect(ray).Vertices()]
            if not distances:
                continue
            actual=min(distances)
            expected=(r*math.sqrt(2)/(math.cos(a)+abs(math.sin(a))) if abs(theta)<45 else r)
            assert abs(actual-expected)<1.e-4,(name,feature,theta,actual,expected)
            checks[str(theta)]=round(actual,5)
        assert set(["-22.5","0.0","22.5","90.0","180.0","270.0"])<=set(checks),(feature,checks)
        results.append(dict(part=name,feature=feature,section_mm=center,axis=axis,
                     radius_mm=r,roof_angle_deg=45.,nominal_round_working_arc_deg=270.,
                     ray_boundary_distances_mm_from_build_up_deg=checks))
    (HERE/"horizontal-bores.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf8")
    print("Seven horizontal bore stations verified")


if __name__=="__main__":
    main()
