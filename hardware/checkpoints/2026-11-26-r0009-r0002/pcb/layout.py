"""Replace only the mechanical drawing of the registered routed case board."""
from pathlib import Path
import math
import sys
import uuid

HERE = Path(__file__).resolve().parent
PARENT = HERE.with_name("case-board-r0001")
sys.path.insert(0, str(PARENT))
from build import emit, items, one, parse

# Installed XY coordinates in millimetres. KiCad's origin is (+87, +114).
LIMITS = (6.5, -16.8, 38.9, 19.0)
RADIUS = 1.5
SCREWS = [(36.0, -14.4), (10.5, 3.9)]
REST = (37.5, 19.85)

def edge(kind, points, index):
    row = [kind]
    for name, (x, y) in points:
        row.append([name, f"{x+87:.6f}", f"{y+114:.6f}"])
    uid = uuid.uuid5(uuid.NAMESPACE_URL, f"thaiwaters:rect-board-r2:edge:{index}")
    return row + [["stroke", ["width", "0.05"], ["type", "default"]],
                  ["layer", '"Edge.Cuts"'], ["uuid", f'"{uid}"']]

def write():
    board = parse(PARENT / "case-board.kicad_pcb")
    board[:] = [p for p in board if not (isinstance(p,list) and items(p,"layer")
                                         and one(p,"layer")[1]=='"Edge.Cuts"')]
    x,y,X,Y = LIMITS
    r=RADIUS
    centers=[(X-r,y+r),(X-r,Y-r),(x+r,Y-r),(x+r,y+r)]
    previous=(x+r,y)
    for i,(cx,cy) in enumerate(centers):
        def point(degrees):
            a=math.radians(degrees)
            return cx+r*math.cos(a),cy+r*math.sin(a)
        start=point(90*i-90)
        mid=point(90*i-45)
        end=point(90*i)
        board.append(edge("gr_line",[("start",previous),("end",start)],2*i))
        board.append(edge("gr_arc",[("start",start),("mid",mid),("end",end)],2*i+1))
        previous=end
    for i,(cx,cy) in enumerate(SCREWS):
        board.append(edge("gr_circle",[("center",(cx,cy)),("end",(cx+1.15,cy))],8+i))
    (HERE/"case-board.kicad_pcb").write_text("("+board[0]+"\n"+"\n".join(map(emit,board[1:]))+"\n)\n",encoding="utf8")

if __name__=="__main__":
    write()

