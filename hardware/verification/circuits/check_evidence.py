"""Independently check retained evidence and five closed-form reference circuits."""
from pathlib import Path
import hashlib, json, math, zipfile
from run import ROOT

def main():
    results=json.loads((ROOT/'results.json').read_text())
    cases={c['id']:c for c in results['cases']}
    with zipfile.ZipFile(ROOT/'raw-ngspice.zip') as logs:
        assert logs.testzip() is None
        assert set(logs.namelist())=={n+'.log' for n in cases}
    for c in cases.values():
        deck=ROOT/c['deck']
        assert hashlib.sha256(deck.read_bytes()).hexdigest()==c['deck_sha256']
    checks=[
        ('i2c_encoder_only','30-70% rise',math.log(.7/.3)*10000*100e-12*1e9),
        ('usb_play_charge','Minimum PMIC input',5-.25*.5),
        ('cc_default','CC voltage',5*5100/(56000+5100)),
        ('speaker_cue','Speaker average real power',(1.4**2)/(2*6)),
        ('erm_running_equivalent','Peak drive current',1000*3/50),
    ]
    proof=[]
    for ident,label,analytical in checks:
        m=next(x for x in cases[ident]['metrics'] if x['label']==label)
        error=abs(m['value']-analytical)/analytical
        assert error<.005,(ident,error)
        proof.append(dict(case=ident,metric=label,unit=m['unit'],solver=m['value'],closed_form=analytical,relative_error=error))
    totals={s:sum(v['status']==s for c in cases.values() for v in c['metrics']) for s in ['WITHIN','OUTSIDE','CHARACTERIZE']}
    record=dict(decks=len(cases),families=len(set(c['family'] for c in cases.values())),metric_counts=totals,
                stored_raw_logs=len(cases),raw_crc='verified',verified_closed_form=proof,
                raw_sha256=hashlib.sha256((ROOT/'raw-ngspice.zip').read_bytes()).hexdigest())
    (ROOT/'validation.json').write_text(json.dumps(record,indent=2)+'\n')
    print('PASS retained log CRCs, case hashes, metric inventory and 5 independent analytical checks.')
if __name__=='__main__':main()
