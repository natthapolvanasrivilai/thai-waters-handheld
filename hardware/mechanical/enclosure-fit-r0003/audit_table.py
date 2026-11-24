"""Make the first-article traveller from all native toolpath and wall-thickness results."""
from pathlib import Path
import csv,json
from collections import Counter
HERE=Path(__file__).resolve().parent
CHECKS=[
'Remove support at the receiver and inside the case. Inspect the roots of every post. Hand-start fasteners in prepared pilots and check each for splitting.',
'Place over the A1 gauge. Check for rocking, glass pressure and head projection. Remove and refit all four screws.',
'Remove support from the accessible face and around the hinge. Inspect both ends of the crank pocket. Rotate fully with crank folded and extended.',
'Cut the brim while supporting the hinge. Inspect the eye, then cycle the pivot by hand.',
'Check grip rotates freely and stays on its axle.','Check collar retention and full-turn clearance.',
'Insert from inside before the switch PCB. Check for twisting, binding and free return.',
'Inspect the thin keeper and cycle the grip screw.','Check nut capture and grip screw alignment without forcing.',
'Check the KEY board remains seated and the plunger returns.','Check the bridge closes over dummy leads without imprints.',
'Slide into the receiver, lock and remove by hand. Inspect the dovetail for peeling.',
'Inspect bends after brim removal. Check the charge channel with an external light.',
'Inspect bends after brim removal. Check the USB channel with an external light.',
'Inspect bends after brim removal. Check the power channel with an external light.',
'Peel the flexible mask from its wide edge. Test the USB-C shell and cable insertion.',
'Check edge integrity, access coverage and removal without tearing.',
'Test maximum pack with dummy lead slack and connector. Remove before trying the other pack.',
'Test PCM, tail and lead exit in the alternative configuration. Use one gauge at a time.',
'Measure underside for sag. Seat at four controller mounts and verify screen position and pressure.',
'Check reel-wall lands and pin registration. Compare with real A2 when available.',
'Check bare board seats flat on the two integral rails. Remove before fitting the mated gauge.',
'Package side down. Inspect all three supports and both screw positions. Check display lift.',
'Install after keyed cap. Check switch orientation and alignment.',
'Check carrier slides into shelf; establish the soldered lead installation order on a real subassembly.',
'Check tiny resistor carrier lands with the USB lamp gauge. Keep both gauges in a parts tray.',
'Inspect flat underside, arm and rails. Drop inboard, slide to USB wall, fit one M2 × 6 and check clearance to speaker.',
'Check oval rim, gasket height and lead exits. Inspect space under lamp shelf.',
'Check motor body, cable exit and board clearance.',
'Install in place of bare A3. Seat A1 and inspect plug space. Verify unlatching and extraction separately with a wired sample.'
]
def run():
    rows=json.loads((HERE/'part-paths.json').read_bytes())
    thick={i['name']:i for i in json.loads((HERE/'thickness.json').read_bytes())}
    assert len(rows)==len(thick)==len(CHECKS)==30
    with (HERE/'first-article.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(['plate','printed part','model layers','first layer contact mm2','support mm3','unbacked starts','vertical wall P05 mm','handling and fit check','physical result'])
        for r,check in zip(rows,CHECKS):
            b=r['model_component_backing'];t=thick[r['name']]
            w.writerow([r['plate'],r['name'],b['layers'],r['first_model_contact_mm2'],r['support_mm3'],len(b['fully_unbacked_components']),t['upright'].get('p05_mm',''),check,'Awaiting R0003 print'])
if __name__=='__main__':run()
