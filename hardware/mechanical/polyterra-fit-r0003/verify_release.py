"""Reopen and verify a complete Bambu slice and the eight independent plate slices."""
from print_project import OUT,HERE,PARENT
from pathlib import Path
import sys
import verify
from channels import verify as openings
import json
verify.OUT=OUT
verify.HERE=HERE
if __name__=='__main__':
    directory=Path(sys.argv[1]).resolve()
    verify.run(directory)
    for n,name in ((0,'full'),(1,'single')):
        rows=openings(directory/f'final{n}'/'plate_1.gcode')
        assert len(rows)==12 and all(r['rim_model_layers'] and max(r['max_mm2'].values())<.001 for r in rows),rows
        (HERE/f'channels-{name}.json').write_text(json.dumps(rows,indent=2)+'\n')
