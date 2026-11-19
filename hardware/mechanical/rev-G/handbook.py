"""Publish the mechanical revision over the frozen electrical and commercial review."""
import argparse,base64,gzip,hashlib,json,re,shutil
from pathlib import Path
here=Path(__file__).resolve().parent
repo=here.parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--exports',required=True,type=Path);out=parser.parse_args().exports
baseline=(out/'Riffle-Rev-F-engineering-review.html').read_bytes()
assert hashlib.sha256(baseline).hexdigest()=='678b3ab78a0e77039d7164cfde3818e05ddec886b7cba482d830f27fa7734a0f'
page=baseline.decode('utf-8'); prefix='https://github.com/natthapolvanasrivilai/thai-waters-handheld'
def script(name):
    return re.search(fr'<script id="{name}"[^>]*>(.*?)</script>',page,re.S)
match=script('reviewData'); data=json.loads(match[1])
stats=json.loads((here/'collisions.json').read_text())['drawing']
qa=json.loads((here/'qualification.json').read_text())
gaps=qa['seated_distance_mm']
data['decisions'][0]='Print the Rev G housing, west key keeper and wire bridge. Both maximum pack shapes now clear the shell and fit through the open top. Use the inert gauges to verify the printed sample, lead dressing and supplier-required pack allowance before powered closure.'
data['fit'][4:5]=[['Drawing maximum → bridge',str(gaps['cellDrawing']['bridge'])+' mm','35.3 × 62.3 × 5.3 mm pack. Minimum modeled bridge clearance with the pack seated on 0.50 mm mounting strips.'],['Supplier CAD → closest PH body',str(gaps['cellAlt']['packplug'])+' mm','Larger cap and lead-stub envelope at the registered seated position.']]
data['fitNotes']=[
 f"{stats['pair_tests']:,} relevant seated pairs checked per pack configuration. No unresolved interference above 0.002 mm³ for the catalog body, drawing maximum or alternate supplier solid.",
 'Two maximum pack envelopes passed their continuous vertical insertion sweeps and sixteen sampled placement corners. Install the controller and bridge after the pack.',
 'Use the new west-side key keeper and two M2 × 4 bridge screws. Select Battery bay in the viewer to change pack and lead geometry. Both 100 mm factory leads are retained.',
 'Five local wall sections measured 1.91–2.50 mm. The housing extends 5.20 mm farther at the rounded turnaround. Printed tolerances, actual lead stiffness, cell allowance and powered charging remain open.'
]
data['collisions']=[dict(first=r['first'],second=r['second'],status=r['status'],overlap_mm3=r['mm3']) for r in stats['intersections']]
data['explodedImage']='data:image/png;base64,'+base64.b64encode((out/'Riffle-Rev-G-battery-bay.png').read_bytes()).decode()
data['productionIntro']='For the next fit print, follow the Rev G pocket procedure and use two inert gauges. The electrical and commercial baseline below is Rev F. The additional bridge, screws and tape allowances are documented in the Rev G fit BOM; volume costs require requoting after sample acceptance.'
data['correlation'][-1][-1]='Check both gauges on the printed Rev G shell; record the pack, lead and mounting material as received, then verify the closed stack.'
data['manifest'].extend([['Rev G maximum-pack study','hardware/mechanical/rev-G/qualification.json'],['Rev G print hashes','hardware/mechanical/rev-G/print-manifest.json']])
page=page[:match.start(1)]+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+page[match.end(1):]
model=script('compressedModel'); embedded=base64.b64encode(gzip.compress((out/'Riffle-Rev-G-exploded.html').read_bytes(),mtime=0)).decode()
page=page[:model.start(1)]+embedded+page[model.end(1):]
game=script('compressedGame')
playable=base64.b64encode(gzip.compress((repo/'game/Thai-Waters-play.html').read_bytes(),mtime=0)).decode()
page=page[:game.start(1)]+playable+page[game.end(1):]
page=page.replace('Personal engineering project · Rev F','Rev G fit print · Rev F electronics').replace('Populated Rev F assembly','Rev G battery fit and assembly').replace('Rev F exploded mechanical assembly viewer','Rev G exploded mechanical assembly viewer').replace("src='Riffle-Rev-F-exploded.html'","src='Riffle-Rev-G-exploded.html'").replace('Riffle Pocket · Rev F · Firmware 0.7','Riffle Pocket · Rev G fit / Rev F electronics · Firmware 0.7')
links='<p><a href="'+prefix+'/releases/download/rev-g-fit-print/Riffle-Rev-G-fit-print.zip">Download Rev G print kit and both inert gauges</a> · <a href="'+prefix+'/blob/main/hardware/mechanical/rev-G/README.md">Fit instructions and collision results</a></p>'
page=page.replace('<h2>Rev G battery fit and assembly</h2>','<h2>Rev G battery fit and assembly</h2>'+links).replace('<h2>Engineering release decision</h2>','<h2>Engineering release decision</h2>'+links)
file=out/'Riffle-Rev-G-handbook.html';file.write_text(page,encoding='utf-8');shutil.copyfile(file,repo/'docs/index.html')

