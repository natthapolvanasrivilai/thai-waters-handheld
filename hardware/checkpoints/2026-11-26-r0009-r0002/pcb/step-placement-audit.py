import re, csv, hashlib, json
from pathlib import Path
base = Path(__file__).parent
step = (base/'case-board-r0002/case-board.step').read_bytes()
assert hashlib.sha256(step).hexdigest() == '123265be74fc5d84e8817ae4a1db8584747d31dea9e75454d0bd53beed9024ac'
manifest = (base/'placement-review.csv').read_bytes()
assert hashlib.sha256(manifest).hexdigest() == '2a9e9eae7153cce90b7ffc33ca6bca48e7b2b86722cd0f4e7dce0942fec65d1a'
rows = list(csv.DictReader(manifest.decode().splitlines()))
refs = re.findall(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+','([A-Z]+\d+)','',#5,", step.decode())
assert len(refs) == len(set(refs))
active_models = {r['reference'] for r in rows if r['model_reference'] and not r['reference'].startswith('W')}
assert set(refs) == active_models
j = [r['reference'] for r in rows if r['reference'].startswith('J')]
w = [r['reference'] for r in rows if r['reference'].startswith('W')]
assert len(j)==13 and len(w)==7 and len(refs)==30
assert all(not r['model_reference'] for r in rows if r['reference'] in j)
assert all(r['model_reference'] for r in rows if r['reference'] in w)
assert b'SolderWire-' not in step
print(json.dumps({'scope':'STEP named root component occurrence vs archived placement manifest, not transform or physical envelope verification',
  'named_component_refs':sorted(refs),'omitted_bare_lands':sorted(j),
  'omitted_generic_wire_refs':sorted(w),'omitted_used_wire_refs':sorted(set(w)-{'W106'}),
  'omitted_isolated_spare':'W106'}, indent=2))
