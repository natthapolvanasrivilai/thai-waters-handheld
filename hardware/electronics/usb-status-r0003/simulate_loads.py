"""R0003 output and shared bus comparison. Run with python simulate_loads.py --engine ngspice.exe."""
from pathlib import Path
import argparse, csv, math, re, subprocess, tempfile, zipfile
ROOT=Path(__file__).resolve().parent/'simulation'
def run(exe,archive,tmp,name,net):
    f=ROOT/(name+'.cir')
    f.write_text(name+' / R0003 / engineering behavioral envelope\n'+net+'\n.END\n')
    out=tmp/(name+'.log')
    proc=subprocess.run([str(exe),'-b','-o',str(out),str(f)],capture_output=True)
    log=out.read_text(errors='replace')
    if proc.returncode or 'Error' in log:raise RuntimeError(log[-1500:])
    archive.write(out,out.name)
    rows=[]
    for line in log.splitlines():
        c=line.split()
        if len(c)==3 and c[0].isdigit():rows.append((float(c[1]),float(c[2])))
    if len(rows)<10:raise ValueError(name+' no trace')
    return rows
def cross(data,level):
    for (t0,y0),(t1,y1) in zip(data,data[1:]):
        if y0<level<=y1:return t0+(t1-t0)*(level-y0)/(y1-y0)
    raise ValueError('threshold missing')
def rms(data):
    dt=data[-1][0]-data[0][0]
    return math.sqrt(sum((t1-t0)*(a*a+b*b)/2 for (t0,a),(t1,b) in zip(data,data[1:]))/dt)
def main():
    p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);exe=p.parse_args().engine.resolve()
    result=[]
    def record(c,metric,value,unit,limit,kind):
        result.append((c,metric,round(value,5),unit,limit,kind))
    with tempfile.TemporaryDirectory() as d,zipfile.ZipFile(ROOT/'load-engine-logs.zip','w',zipfile.ZIP_DEFLATED) as archive:
        tmp=Path(d)
        for name,v,r in [('audio_nominal',3.3,8),('audio_gain_boundary',3.6,8),('audio_low_impedance',3.3,6.4)]:
            q=run(exe,archive,tmp,name,f"""VPA plus 0 SIN(1.95 {v/2} 1000)
VPB minus 0 SIN(1.95 {-v/2} 1000)
Rspeaker plus minus {r}
.TRAN 3u 12m 2m 3u
.PRINT TRAN V(plus,minus)""")
            vout=rms(q);power=vout*vout/r
            record(name,'Differential RMS',vout,'Vrms',2.52982 if r==8 else 'per measured impedance','bench comparison')
            record(name,'Resistive load power',power,'W',.8,'within screen' if power<=.8 else 'above screen')
        v=138*.02159
        for name,r,back,l in [('motor_low_DCR_stall',26.4,0,.001),('motor_high_DCR_stall',78,0,.003),('motor_nominal_running_equivalent',33,1.0,.001)]:
            q=run(exe,archive,tmp,name,f"""Vdrive drive 0 PULSE(0 {v} 1m 2u 2u 18m 40m)
Rwinding drive coil {r}
Lwinding coil em {l}
Vbemf em 0 PULSE(0 {back} 1m 2u 2u 18m 40m)
.TRAN 10u 17m
.PRINT TRAN I(Vdrive)""")
            med=max(-i for t,i in q)*1000
            record(name,'Motor peak in model',med,'mA',60 if 'running' in name else 'inrush: measure','screen' if 'running' in name else 'characterize')
        for name,pulls,c in [('bus_driver_encoder_100p',[2200,10000],100),('bus_driver_encoder_200p',[2200,10000],200),('bus_optional_4k7_200p',[2200,10000,4700],200),('bus_unexpected_820ohm_100p',[820],100)]:
            resistors='\n'.join(f'R{i} source line {r}' for i,r in enumerate(pulls,1))
            q=run(exe,archive,tmp,name,f"""Vrelease source 0 PULSE(0 3.3 1u 100p 100p 14u 30u)
{resistors}
Cbus line 0 {c}p
.TRAN 1n 4u 0 2n
.PRINT TRAN V(line)""")
            tr=(cross(q,.7*3.3)-cross(q,.3*3.3))*1e9
            sink=2.9*sum(1/r for r in pulls)*1000
            record(name,'30–70 percent rise time',tr,'ns',300,'within screen' if tr<=300 else 'above screen')
            record(name,'Calculated sink at 0.4 V',sink,'mA',3,'within screen' if sink<=3 else 'above screen')
    with (ROOT/'load-results.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(('case','metric','value','unit','screen','interpretation'));writer.writerows(result)
    print(len(result),'metrics')
if __name__=='__main__':main()
