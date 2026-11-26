"""Reproduce the prior seated-display failure on native solids and compare identical stations."""

import cadquery as cq

from assemble import HERE, ELECTRONICS, WIRES, load, save, digest
from service_check import native_gap
from stroke import new_leads
import mate as previous_leads

def sample(route_model, route, board, d):
    tx,_,z=route["SCL"]["tap_center_mm"]
    lead=route_model.jacket("SCL",tx,z,d)[0]
    return {**native_gap(lead,board), "common_mm3":round(lead.intersect(board).Volume(),7)}

if __name__=="__main__":
    old=ELECTRONICS/"harness-r0005"
    cases={}
    for label,route_model,h,board in [
        ("R0012",previous_leads,old,old/"placed/A5-power.brep"),
        ("R0013",new_leads(),WIRES,ELECTRONICS/"usb-entry-r0006/A5-power.brep")
    ]:
        solid=cq.Shape.importBrep(str(board))
        routes=load(h/"routing.json")
        values={str(d):sample(route_model,routes,solid,d) for d in (0,.375,.5,4.125,8.25)}
        cases[label]={"board_sha256":digest(board),"routing_sha256":digest(h/"routing.json"),"stations_mm":values}
    old_hit=cases["R0012"]["stations_mm"]["0.5"]
    assert old_hit["common_mm3"]>0
    (HERE/"QA").mkdir(exist_ok=True)
    save(HERE/"QA/installed-negative-control.json",cases)
    print(cases)
    assert all(v["gap_mm"]>0 and v["common_mm3"]==0 for v in cases["R0013"]["stations_mm"].values())
