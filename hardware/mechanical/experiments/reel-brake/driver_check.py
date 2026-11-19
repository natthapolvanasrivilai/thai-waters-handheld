"""Generate and run the bench driver's electrical bounds, export raw ngspice print tables."""
from pathlib import Path
import argparse, subprocess, csv, json, os, tempfile, zipfile, hashlib
ROOT=Path(__file__).resolve().parent
CASES=[('nominal',5,4.5,.010),('peak_cold',5.25,4.275,.003),('slow_release',4.75,4.725,.030)]
def trace(text):
    cols={};fields=[]
    for line in text.splitlines():
        v=line.split()
        if v[:2]==['Index','time']: fields=v[2:];continue
        if not fields or len(v)!=len(fields)+2 or not v[0].isdigit():continue
        t=float(v[1])
        for name,voltage in zip(fields,v[2:]):cols.setdefault(name,{})[t]=float(voltage)
    return {k:sorted(a.items()) for k,a in cols.items()}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--engine',required=True,type=Path);opt=ap.parse_args()
    exe=opt.engine.resolve(); rows=[]
    with tempfile.TemporaryDirectory() as temp:
        temp=Path(temp)
        with zipfile.ZipFile(ROOT/'driver-traces.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for label,vs,r,l in CASES:
                deck=ROOT/('brake-'+label+'.cir')
                deck.write_bytes(('\n'.join([
                    'B0 tabletop snag-brake coil - '+label,
                    '* Engineering substitutions: 0.1 ohm supply/harness, assumed L, ideal 5V 105ms one-shot.',
                    '* NMOS DC slope approximates driver; diode surrogate. Timing chip and plunger mechanics are outside deck.',
                    f'Vs supply 0 {vs}','Rh supply feed 0.1','Vcoil feed high 0',f'Rw high w {r}',f'L1 w drain {l}',
                    'M1 drain gate 0 0 md W=1u L=1u','.MODEL md NMOS(LEVEL=1 VTO=1.5 KP=4)',
                    'D1 drain feed df','.MODEL df D(IS=1e-9 N=1.5 RS=.05)','Roff drain 0 100meg',
                    'Vg gate 0 DC 0 PULSE(0 5 5m 1u 1u 105m 3)','Rpd gate 0 100k',
                    '.TRAN 50u 160m 0 50u','.PRINT TRAN I(Vcoil) V(drain)','.END',''])).encode('ascii'))
                log=temp/(label+'.log')
                subprocess.run([str(exe),'-b','-o',str(log),str(deck)],cwd=temp,timeout=25,check=True,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                txt=log.read_text(errors='replace')
                if 'Error:' in txt:raise RuntimeError(txt[:2000])
                ws=trace(txt);curr=ws['vcoil#branch'];vdr=ws['v(drain)']; peak=max(i for t,i in curr)
                falling=110.001e-3
                end=next(t for t,i in curr if t>falling and i<=.1*peak)
                energy=sum((b-a)*(i*i+i*j+j*j)*r/3 for (a,i),(b,j) in zip(curr,curr[1:]))
                rows.append({'case':label,'supply_V':vs,'coil_R_ohm':r,'assumed_L_mH':l*1000,
                             'peak_A':round(peak,4),'peak_drain_V':round(max(v for t,v in vdr),4),
                             'winding_J_per_event':round(energy,4),'current_to_10_percent_ms':round((end-falling)*1000,3),
                             'average_winding_W_at_one_event_per_2p4s':round(energy/2.4,4)})
                archive.write(log,log.name)
    (ROOT/'driver-results.json').write_text(json.dumps({'engine':'ngspice','engine_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'cases':rows},indent=2)+'\n')
    print(json.dumps(rows,indent=1))
if __name__=='__main__': main()
