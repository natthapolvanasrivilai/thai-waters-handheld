"""Export compact, peak-preserving plotting traces from the archived solver log."""
import json, zipfile
from run import ROOT,series

PLOTS=[
    ('Shared I2C rise', 'us','V',1e6,1,'V(bus)', ['i2c_encoder_only','i2c_encoder_motor','i2c_additional_4k7','i2c_loaded_200pf']),
    ('3.3 V transient', 'us','V',1e6,1,'V(rail)', ['rail_typ_assumed','rail_derated_slow']),
    ('Battery connector under load', 'ms','V',1e3,1,'V(j7)', ['bat_fresh','bat_mid','bat_low_aged']),
    ('Sealed thermal sensitivity', 'min','deg C',1/60,1,'V(hot)', ['thermal_vented_assumption','thermal_sealed_stress']),
    ('Speaker differential swing', 'ms','V',1e3,1,'V(diff)', ['speaker_cue','speaker_near_rating','speaker_overdrive']),
    ('Motor-current envelope', 'ms','mA',1e3,-1000,'I(Vdrive)', ['erm_running_equivalent','erm_low_R_start','erm_locked_stress']),
    ('USB full-speed receiver', 'ns','V',1e9,1,'V(dp)', ['usbdata_nominal','usbdata_heavy_fixture']),
]
def sample(points,n=100):
    # Retain each time bucket's extremes in chronological order, as well as endpoints.
    if len(points)<=n:return points
    buckets=max(1,(n-2)//2);start=points[0][0];end=points[-1][0]
    groups=[[] for _ in range(buckets)]
    for point in points:groups[min(buckets-1,int((point[0]-start)/(end-start)*buckets))].append(point)
    keep={points[0],points[-1]}
    for group in groups:
        if group:keep.update((min(group,key=lambda q:q[1]), max(group,key=lambda q:q[1])))
    return sorted(keep)
def main():
    cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())}
    plots=[]
    with zipfile.ZipFile(ROOT/'raw-ngspice.zip') as raw:
        for title,tu,vu,xt,yt,field,ids in PLOTS:
            traces=[]
            for name in ids:
                points=series(raw.read(name+'.log').decode(errors='replace'),cases[name]['outputs'])[field.lower()]
                traces.append(dict(id=name,model=cases[name]['description'],points=[[float(f'{t*xt:.6g}'),float(f'{v*yt:.6g}')] for t,v in sample(points)]))
            plots.append(dict(title=title,time_unit=tu,value_unit=vu,measured=field,traces=traces))
    (ROOT/'waveforms.json').write_text(json.dumps(plots,separators=(',',':'))+'\n')
if __name__=='__main__':main()
