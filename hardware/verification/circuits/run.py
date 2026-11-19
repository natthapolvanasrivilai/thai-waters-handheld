"""Run the desktop SPICE regression with ngspice. Python 3.10+, standard library."""
import argparse, csv, hashlib, json, math, os, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def series(text, outputs):
    # .PRINT tables can be split over several pages or several variable groups.
    columns={name.lower():{} for name in outputs}
    fields=[]
    for line in text.splitlines():
        words=line.split()
        if len(words)>2 and words[0]=='Index' and words[1]=='time':
            fields=[re.sub(r'^(.+)#branch$',r'i(\1)',w.lower()) for w in words[2:]]
        elif fields and len(words)==len(fields)+2 and words[0].isdigit():
            t=float(words[1])
            for name, val in zip(fields,words[2:]):
                if name in columns:columns[name][t]=float(val)
    if any(len(trace)<2 for trace in columns.values()):
        raise ValueError(f'Missing printed columns: {[(k,len(v)) for k,v in columns.items()]}')
    return {key:sorted(v.items()) for key,v in columns.items()}

def crossing(points,level):
    for (t0,v0),(t1,v1) in zip(points,points[1:]):
        if v0<=level<v1:return t0+(t1-t0)*(level-v0)/(v1-v0)
    raise ValueError(f'No rising crossing of {level}')

def measure(points, spec):
    op=spec['calculation'];vals=[v for _,v in points]
    if op=='last': val=vals[-1]
    elif op=='min': val=min(vals)
    elif op=='absmax': val=max(map(abs,vals))
    elif op=='rise': val=crossing(points,spec['high'])-crossing(points,spec['low'])
    elif op=='cross': val=crossing(points,spec['level'])-spec['origin']
    elif op=='resistive_power':
        start=spec['start']; end=points[-1][0]; energy=0
        for (a,u),(b,v) in zip(points,points[1:]):
            if b<=start:continue
            if a<start:
                u += (v-u)*(start-a)/(b-a);a=start
            energy+=(b-a)*(u*u+u*v+v*v)/(3*spec['resistance'])
        val=energy/(end-start)
    else:raise ValueError(op)
    val*=spec.get('scale',1)
    if not math.isfinite(val):raise ValueError('Non-finite measurement')
    bounds=spec['limits']
    status='CHARACTERIZE' if bounds is None else 'WITHIN' if bounds[0]-1e-8<=val<=bounds[1]+1e-8 else 'OUTSIDE'
    return dict(label=spec['label'],value=float(f'{val:.7g}'),unit=spec['unit'],limits=bounds,status=status)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',default='ngspice')
    parser.add_argument('--engine-version',required=True,help='Exact version of the ngspice build being used')
    opt=parser.parse_args();exe=Path(shutil.which(opt.engine) or opt.engine).resolve()
    cases=json.loads((ROOT/'cases.json').read_text())
    result=dict(engine='ngspice '+opt.engine_version,engine_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                cadence_status='Native Cadence PSpice run pending',cases=[])
    with tempfile.TemporaryDirectory() as scratch:
        work=Path(scratch)
        for case in cases:
            name=case['id']
            deck=ROOT/case['deck'];log=work/(name+'.log')
            subprocess.run([str(exe),'-b','-o',str(log),str(deck)],cwd=work,check=True,timeout=45,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            diagnostic=log.read_text(encoding='utf-8',errors='replace')
            if re.search(r'^\s*(?:fatal|error)\b|simulation\(s\) aborted|timestep too small',diagnostic,re.I|re.M):
                raise RuntimeError(name+': '+diagnostic[:2000])
            trace=series(diagnostic,case['outputs'])
            observed={key:case[key] for key in ['id','family','description','sources','model','deck']}
            observed['deck_sha256']=hashlib.sha256(deck.read_bytes()).hexdigest()
            observed['metrics']=[measure(trace[m['column'].lower()],m) for m in case['metrics']]
            result['cases'].append(observed)
        with zipfile.ZipFile(work/'raw.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as raw:
            for log in sorted(work.glob('*.log')):raw.write(log,log.name)
        shutil.copyfile(work/'raw.zip',ROOT/'raw-ngspice.zip')
    (ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'results.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.writer(stream);writer.writerow(['case','family','metric','value','unit','limit_min','limit_max','status','deck','sources'])
        for c in result['cases']:
            for m in c['metrics']:writer.writerow([c['id'],c['family'],m['label'],m['value'],m['unit'],*(m['limits'] or ['','']),m['status'],c['deck'],' | '.join(c['sources'])])
    print(f"Executed {len(cases)} decks and {sum(len(c['metrics']) for c in result['cases'])} metrics.")
if __name__=='__main__': main()
