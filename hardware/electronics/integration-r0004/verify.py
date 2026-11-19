"""Replay historical circuits without changing them, then run R0004 interface corners."""
import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from corners import circuits

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / 'verification' / 'circuits'
R3 = HERE.parent / 'usb-status-r0003'
BRAKE = HERE.parents[1] / 'mechanical' / 'experiments' / 'reel-brake'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source))

def historical(exe, tmp, archive):
    groups = [(BASE, 'legacy', ['run.py', 'results.csv', 'cases.json'], 'run.py', 'results.csv', 'raw-ngspice.zip'),
              (R3, 'loads', ['simulate_loads.py'], 'simulate_loads.py', 'simulation/load-results.csv', 'simulation/load-engine-logs.zip'),
              (R3, 'indicator', ['simulate.py'], 'simulate.py', 'simulation/results.csv', 'simulation/engine-logs.zip'),
              (BRAKE, 'brake', ['driver_check.py'], 'driver_check.py', 'driver-results.json', 'driver-traces.zip')]
    report = {}
    for source, group, files, runner, output, raw in groups:
        folder = tmp / group
        folder.mkdir()
        for filename in files:
            shutil.copyfile(source / filename, folder / filename)
        if group == 'legacy':
            shutil.copytree(source / 'decks', folder / 'decks')
        if source == R3:
            (folder / 'simulation').mkdir()
        cmd = [sys.executable, runner, '--engine', str(exe)]
        if group == 'legacy':
            cmd.extend(['--engine-version', '33'])
        subprocess.run(cmd, cwd=folder, capture_output=True, check=True, timeout=300)
        if output.endswith('json'):
            old = json.loads((source / output).read_text())['cases']
            new = json.loads((folder / output).read_text())['cases']
        else:
            old, new = rows(source / output), rows(folder / output)
        if old != new:
            raise ValueError(f'{group} scalar replay differs from archive')
        with zipfile.ZipFile(folder / raw) as logs:
            if logs.testzip() is not None:
                raise ValueError(f'{group} log CRC')
            for key in logs.namelist():
                archive.writestr(f'control/{group}/{key}', logs.read(key))
        deck_inventory = {}
        for deck in sorted(folder.rglob('*.cir')):
            relative = deck.relative_to(folder)
            if deck.read_text() != (source / relative).read_text():
                raise ValueError(f'{relative} control deck differs')
            deck_inventory[relative.as_posix()] = digest(source / relative)
        report[group] = dict(cases=len(deck_inventory), deck_sha256=deck_inventory, scalar_rows=len(new))
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', required=True, type=Path)
    exe = parser.parse_args().engine.resolve()
    known_engine = '54068911555d46067ff2bdfcd0cf4b1afd3c1330be0586f93911df0a6af88e7c'
    if digest(exe) != known_engine:
        raise RuntimeError('Historic scalar comparator requires ngspice-33')
    results = []
    with tempfile.TemporaryDirectory() as work:
        tmp = Path(work)
        with zipfile.ZipFile(tmp/'evidence.zip','w',zipfile.ZIP_DEFLATED) as archive:
            controls = historical(exe, tmp, archive)
            for name, net, analysis, specs in circuits():
                if name in {r['case'] for r in results}:
                    raise ValueError('Duplicate case ' + name)
                deck = tmp / (name + '.cir')
                log = tmp / (name + '.log')
                measures = ['.meas tran ' + tag + ' ' + cmd for tag, cmd, _, _, _ in specs]
                probes = sorted({probe.lower() for _,cmd,_,_,_ in specs for probe in re.findall(r'[vi]\([a-z][a-z0-9_]*\)', cmd, re.I)})
                table = '.print tran ' + ' '.join(probes)
                deck.write_bytes(('\n'.join(['Thai Waters R0004 | ' + name, net, analysis, *measures, table, '.end', ''])).encode('ascii'))
                subprocess.run([str(exe), '-b', '-o', str(log), str(deck)], cwd=tmp, capture_output=True, check=True, timeout=30)
                trace = log.read_text(errors='replace')
                if re.search(r'^\s*(?:fatal|error)\b|failed!|simulation\(s\) aborted|timestep too small', trace, re.M|re.I):
                    raise RuntimeError(name+' '+trace[-1800:])
                if not re.search(r'^Index\s+time\s+',trace,re.M):
                    raise ValueError('No time-domain output in '+name)
                archive.write(deck, 'candidate/'+deck.name)
                archive.write(log, 'candidate/'+log.name)
                for tag, _, unit, low, high in specs:
                    value = float(re.search(r'^'+tag+r'\s*=\s*([0-9.eE+-]+)',trace,re.M)[1])
                    status = 'RECORD' if low is None else 'WITHIN' if low <= value <= high else 'OUTSIDE'
                    results.append(dict(case=name,metric=tag,value=value,unit=unit,lo=low,hi=high,status=status))
        shutil.copyfile(tmp/'evidence.zip', HERE/'solver-evidence.zip')
    with (HERE/'results.csv').open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out,fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    counts = {s:sum(r['status']==s for r in results) for s in ('WITHIN','OUTSIDE','RECORD')}
    summary = dict(engine='ngspice-33', executable_sha256=digest(exe), historical=controls,
                   candidate_cases=len({r['case'] for r in results}),candidate_metrics=counts,
                   evidence_sha256=digest(HERE/'solver-evidence.zip'))
    (HERE/'verification.json').write_text(json.dumps(summary,indent=2)+'\n', encoding='utf-8')
    print(summary['candidate_cases'], counts)
    failures = {(r['case'],r['metric']) for r in results if r['status']=='OUTSIDE'}
    expected = {('diagnostic_'+name,'pmic_v') for name in ('no_cell_default','no_cell_configured','no_cell_grant_loss')}
    expected.add(('diagnostic_previous_play_with_lamp','port'))
    expected.add(('diagnostic_mux_old_termination','rise'))
    if failures != expected:
        raise SystemExit('Unexpected range result in candidate or negative controls; see results.csv')

if __name__ == '__main__':
    main()
