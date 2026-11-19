"""Pack the checked Rev G viewer and the print kit for the private fit release."""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,zipfile
here=Path(__file__).resolve().parent
repo=here.parents[2]
ref=here.parent/'rev-F/review'
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--exports',type=Path,required=True)
a=p.parse_args();out=a.exports.resolve()
report=json.loads((here/'collisions.json').read_text())
checks=dict(revision='G',variants=report,threshold_mm3=.002,**report['drawing'])
page=(ref/'template.html').read_text(encoding='utf-8-sig').replace('>REV F<','>REV G<').replace('value="drawing"','value="drawing" selected').replace('<button data-view="interior">','<button data-view="battery">Battery bay</button><button data-view="interior">')
for key,value in {'MESH':(a.work/'meshes.json').read_text(encoding='utf-8'),'FONT':base64.b64encode((repo/'game/assets/fonts/AtkinsonHyperlegibleNext.ttf').read_bytes()).decode(),'CHECKS':json.dumps(checks,separators=(',',':')),'VIEW':(a.work/'renderer.js').read_text(encoding='utf-8')}.items():
    assert '@@'+key+'@@' in page
    page=page.replace('@@'+key+'@@',value)
page=page.replace('</html>','<!--\n'+(repo/'third-party/three-LICENSE.txt').read_text(encoding='utf-8')+(repo/'game/assets/fonts/OFL.txt').read_text(encoding='utf-8')+'\n-->\n</html>')
doc=repo/'docs/models/Riffle-Rev-G-exploded.html';doc.parent.mkdir(exist_ok=True)
doc.write_text(page,encoding='utf-8');shutil.copyfile(doc,out/doc.name)
files={f'Print/{f.name}':f for f in (here/'Print').glob('*.stl')}
files.update({f'Inert-gauges/{f.name}':f for f in (ref/'gauges').glob('*.stl')})
for f in ('README.md','collisions.json','qualification.json','print-manifest.json','routes.json','fit-bom.csv','parts.json','battery-bay.png','viewer-verification.txt'):files[f]=here/f
assert len([k for k in files if k.startswith('Print/')])==12
with zipfile.ZipFile(out/'Riffle-Rev-G-fit-print.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    manifest=[]
    for name,f in sorted(files.items()):
        raw=f.read_bytes();z.writestr(name,raw);manifest.append(hashlib.sha256(raw).hexdigest()+'  '+name)
    z.writestr('SHA256SUMS.txt','\n'.join(manifest)+'\n')
with zipfile.ZipFile(out/'Riffle-Rev-G-fit-print.zip') as z:assert z.testzip() is None
print(doc, len(page),len(files),'kit files')

