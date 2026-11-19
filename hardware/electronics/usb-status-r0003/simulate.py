"""Solve each USB branch corner with ngspice DC. Ideal LED knee + 10 ohm slope, assumed bins."""
import argparse, csv, hashlib, json, re, subprocess, tempfile, zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent
CASES=[('unplugged',0,2.7,2700,False),('nominal',5.0,2.8,2700,False),('dim',4.4,4.0,2727,False),('bright',5.25,2.15,2673,False),('short_after_R',5.25,0,2673,True)]
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--engine',required=True,type=Path)
    exe=p.parse_args().engine.resolve()
    directory=OUT/'simulation'
    directory.mkdir(exist_ok=True)
    results=[]
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(directory/'engine-logs.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name,vbus,vf,res,short in CASES:
            # Piecewise LED envelope, includes a physical near-open floor (1 Tohm).
            path=directory/(name+'.cir')
            elem='Rshort lamp 0 1m' if short else f'Gled lamp 0 VALUE = {{MAX(0,V(lamp)-{vf})/10}}'
            deck=f"""USB indicator {name} / R0003 / engineering envelopes in volts and ohms
Vusb vbus 0 0
Rlimit vbus lamp {res}
Rleak lamp 0 1T
{elem}
.DC Vusb {vbus:.5f} {vbus+0.0001:.5f} 0.0001
.PRINT DC V(vbus) V(lamp) I(Vusb)
.END
"""
            path.write_text(deck)
            log=Path(tmp)/(name+'.log')
            proc=subprocess.run([str(exe),'-b','-o',str(log),str(path.resolve())],capture_output=True)
            out=log.read_text(errors='replace')
            if proc.returncode or 'Error' in out:raise RuntimeError(out[:1200])
            m=re.search(r'^0\s+([\deE.+-]+)\s+([\deE.+-]+)\s+([\deE.+-]+)\s+([\deE.+-]+)',out,re.M)
            if not m:raise RuntimeError(out[-1500:])
            _,vs,vl,iv=map(float,m.groups());i=-iv
            results.append(dict(case=name,source_V=vs,led_V=vl,current_mA=round(1000*i,5),R_ohm=res,resistor_mW=round(i*i*res*1000,5)))
            archive.write(log,log.name)
    with (directory/'results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=results[0].keys());w.writeheader();w.writerows(results)
    (directory/'engine.json').write_text(json.dumps({'engine':'ngspice-33','exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2)+'\n')
    assert results[0]['current_mA']<0.00001 and max(x['current_mA'] for x in results)<2.0 and max(x['resistor_mW'] for x in results)<11
    print(results)
if __name__=='__main__':main()

