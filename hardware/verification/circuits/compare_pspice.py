"""Compare licensed Cadence .OUT transient PRINT tables against this package.
Usage: python compare_pspice.py ./native-output ./native-comparison.csv
Run files must be named <case-id>.out, generated from the delivered .cir files.
A mismatched or missing table is an error. This tool cannot execute PSpice.
"""
import argparse, csv, hashlib, json, math, re
from pathlib import Path
from run import ROOT, measure

def value(token):
    token=token.strip().lower()
    match=re.fullmatch(r'([+-]?(?:\d+\.?\d*|\.\d+)(?:[ed][+-]?\d+)?)(meg|[tgkmunpf])?',token)
    if not match:raise ValueError(token)
    prefix={None:1,'t':1e12,'g':1e9,'meg':1e6,'k':1e3,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12,'f':1e-15}
    return float(match[1].replace('d','e'))*prefix[match[2]]

def print_tables(text,outputs):
    data={col.upper():{} for col in outputs}
    fields=[]
    for line in text.splitlines():
        words=line.strip().upper().split()
        if not words:continue
        if words[0]=='TIME':
            fields=[word.replace(',0)',')') for word in words[1:]]
            continue
        if not fields or len(words)!=len(fields)+1:continue
        try: nums=[value(w) for w in words]
        except ValueError:continue
        for field,num in zip(fields,nums[1:]):
            if field in data:data[field][nums[0]]=num
    if any(len(trace)<2 for trace in data.values()):raise ValueError('Missing required native TIME / V(...) / I(...) table.')
    return {k:sorted(points.items()) for k,points in data.items()}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('native_folder',type=Path);ap.add_argument('output_csv',type=Path)
    args=ap.parse_args()
    cases=json.loads((ROOT/'cases.json').read_text())
    reference={c['id']:c for c in json.loads((ROOT/'results.json').read_text())['cases']}
    rows=[];pending=[]
    for c in cases:
        name=c['id'];base=reference[name]
        if hashlib.sha256((ROOT/c['deck']).read_bytes()).hexdigest()!=base['deck_sha256']:
            raise RuntimeError(name+': delivered deck changed after reference simulation')
        out=args.native_folder/(name+'.out')
        if not out.exists():pending.append(name);continue
        text=out.read_text(encoding='utf-8',errors='replace')
        if 'PSPICE' not in text.upper() or re.search(r'^\s*ERROR(?:\s|\()',text,re.I|re.M):
            raise RuntimeError(str(out)+': missing native identification or solver error')
        trace=print_tables(text,c['outputs']); native_hash=hashlib.sha256(out.read_bytes()).hexdigest()
        for spec,old in zip(c['metrics'],base['metrics']):
            new=measure(trace[spec['column'].upper()],spec)
            # Project reconciliation criteria. Source values in both engines
            # must retain their status and agree to 2%, with a small zero floor.
            tol=max(.02*abs(old['value']),1e-5)
            agrees=abs(new['value']-old['value'])<=tol and new['status']==old['status']
            rows.append([name,old['label'],old['unit'],old['value'],new['value'],tol,old['status'],new['status'],
                         'AGREES' if agrees else 'REVIEW',base['deck_sha256'],native_hash])
    with args.output_csv.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['case','metric','unit','ngspice','pspice','agreement_tolerance','ngspice_status','pspice_status','agreement','deck_sha256','native_out_sha256']);w.writerows(rows)
    print(f'{len(rows)} native metrics compared; {len(pending)} native runs outstanding.')
    if pending:print('Missing native outputs: '+', '.join(pending))
    if pending or any(r[8]=='REVIEW' for r in rows):raise SystemExit(2)
if __name__=='__main__':main()
