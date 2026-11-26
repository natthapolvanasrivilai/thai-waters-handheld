"""Rerun current custom-board checks in isolation and retain source fingerprints."""
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
import argparse,csv,json,shutil,subprocess,sys,os
HERE=Path(__file__).resolve().parent
ELEC=HERE.parents[1]/'electronics'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def run(cli,spice):
    result={}
    with TemporaryDirectory() as temp:
        root=Path(temp)
        for folder in ('case-board-r0001','pcb-haptic-cie-r0002'):
            src=ELEC/folder
            pcb,=src.glob('*.kicad_pcb')
            sch,=src.glob('*.kicad_sch')
            data={}
            for mode,design,extra in [('erc',sch,[]),('drc',pcb,['--schematic-parity'])]:
                dest=root/(folder+mode+'.json')
                subprocess.run([str(cli),'sch' if mode=='erc' else 'pcb',mode,'--format','json','--severity-error','--severity-warning',*extra,'-o',str(dest),str(design)],check=True)
                r=json.loads(dest.read_bytes())
                data[mode]=dict(source_sha256=sha(design),violations=sum(len(sheet['violations']) for sheet in r['sheets']) if mode=='erc' else len(r['violations']),unrouted=len(r.get('unconnected_items',[])),parity=len(r.get('schematic_parity',[])))
            result[folder]=data
        sys.path.insert(0,str(ELEC/'case-board-r0001'))
        import circuit
        board=ELEC/'case-board-r0001/case-board.kicad_pcb'
        shutil.copyfile(board,root/board.name)
        circuit.HERE=root
        circuit.main(spice)
        r=json.loads((root/'verification.json').read_bytes())
        rows=list(csv.DictReader((root/'measurements.csv').open()))
        result['input_supply']=dict(cases=r['circuit_cases'],measurements=len(rows),statuses=r['statuses'],exceptions=[x for x in rows if x['status']=='OPEN_FAIL'],source_sha256=sha(board))
    (HERE/'electrical.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kicad',type=Path);p.add_argument('spice',type=Path);a=p.parse_args();run(a.kicad.resolve(),a.spice.resolve())
