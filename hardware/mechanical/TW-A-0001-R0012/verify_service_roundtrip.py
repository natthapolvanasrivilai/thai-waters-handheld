"""Independently repeat critical service measurements on the packed installation."""
import argparse
import gzip
import shutil
import tempfile
from pathlib import Path
import cadquery as cq
from build import HERE, load, save, digest
from service_check import HARNESS, native_gap
from mate import actuate, split_latch, STROKE, jacket

def verify(source):
    qa=load(HARNESS/'clearance.json')
    export=load(HERE/'export-verification.json')
    assert digest(source)==export['packed_step_sha256']
    with tempfile.TemporaryDirectory() as temp:
        raw=Path(temp)/'roundtrip.step'
        with gzip.open(source,'rb') as inp,raw.open('wb') as out:shutil.copyfileobj(inp,out)
        assert digest(raw)==export['step_sha256']
        assembly=cq.Assembly.load(str(raw))
    rows={c.name:c.obj.moved(c.loc) for c in assembly.children}
    assert set(rows)==set(load(HERE/'installed-step.json')['components'])
    plug=rows['A3-J1-plug']
    b,l=split_latch(plug)
    assert abs(plug.Volume()-b.Volume()-l.Volume())<.001
    changes=load(HARNESS/'installed.json')['add']
    critical={'A3-J1-header','A3-J1-plug','A3-J1-TPA','drvBoard','A4-integration','A5-power'} | set(qa['W1_stationary_members'])
    valid={k:rows[k].isValid() for k in critical}
    assert all(valid.values())
    sample=qa['rigid_W1_minimum_sample']
    rigid=cq.Compound.makeCompound([b,actuate(l,sample['press_fraction']),*[rows[k] for k in qa['rigid_members'][1:]]]).translate((0,sample['travel_mm'],0))
    repeat=native_gap(rigid,rows[sample['part']])
    assert abs(repeat['gap_mm']-sample['gap_mm'])<.001
    inter=plug.intersect(rows['A3-J1-header'].Solids()[0]).Volume()
    assert abs(inter-sum(x['volume_mm3'] for x in qa['unmodified_seated_plastics_intersections']))<.002
    tpa=plug.intersect(rows['A3-J1-TPA']).Volume()
    assert abs(tpa-qa['plug_to_TPA_overlap_mm3'])<.002
    f=qa['minimum_W4_mesh']; routes=load(HARNESS/'routing.json')
    def lead(net):
        xx,_,zz=routes[net]['tap_center_mm']
        return rows['wh'+net] if f['travel_mm']==0 else jacket(net,xx,zz,f['travel_mm'])[0]
    other=lead(f['W4_part'][2:]) if f['W4_part'].startswith('wh') else rows[f['W4_part']]
    close=native_gap(lead(f['W4_net']),other)
    assert abs(close['gap_mm']-qa['offending_W4_native']['gap_mm'])<.001
    save(HERE/'QA/service-roundtrip.json',dict(assembly=HERE.name,compressed_sha256=digest(source),
        step_sha256=export['step_sha256'],assembly_nodes=len(rows),validity=valid,
        native_minimum_rigid_to_W1=repeat,native_minimum_sampled_flex_pair=close,
        seated_supplier_latch_overlap_mm3=round(inter,6),seated_supplier_TPA_overlap_mm3=round(tpa,6),
        fixed_loom_stationary_components=qa['W1_stationary_members'],
        source_manifest_sha256=digest(HARNESS/'installed.json'),route_sha256=digest(HARNESS/'routing.json')))
    print('Round-trip service evidence verified.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path)
    verify(p.parse_args().archive)

