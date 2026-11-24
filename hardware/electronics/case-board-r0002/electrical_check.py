"""Check all routed objects and footprints against the electrically verified parent."""
import hashlib, json
from collections import Counter
from layout import HERE, PARENT, parse, emit, items, one

def routed(path):
    board=parse(path)
    return [emit(p) for p in board[1:] if not (items(p,'layer') and one(p,'layer')[1]=='"Edge.Cuts"')]

def check():
    board=HERE/'case-board.kicad_pcb'
    same=routed(board)==routed(PARENT/board.name)
    assert same
    pcb=parse(board)
    checks={}
    for name in ['drc','erc']:
        data=json.loads((HERE/(name+'.json')).read_bytes())
        problems=data.get('violations',[])+data.get('unconnected_items',[])+data.get('schematic_parity',[])
        problems.extend(v for page in data.get('sheets',[]) for v in page['violations'])
        assert not problems,problems
        checks[name]=len(problems)
    counts=Counter(p[0] for p in pcb[1:] if isinstance(p,list))
    out={'routed_objects_and_settings_equal_to_parent':same,'footprints':counts['footprint'],'tracks':counts['segment'],'vias':counts['via'],
         'checks':checks,'board_sha256':hashlib.sha256(board.read_bytes()).hexdigest()}
    (HERE/'electrical-check.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':check()
