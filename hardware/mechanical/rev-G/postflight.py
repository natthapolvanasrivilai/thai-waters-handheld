"""Independently re-import the released STEP; check the artifact and unplugging space."""
import argparse,gzip,io,hashlib,json,shutil,zipfile
from pathlib import Path
import cadquery as cq
import trimesh
from geometry import box
here=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--exports',type=Path,required=True)
parser.add_argument('--work',type=Path,required=True)
args=parser.parse_args()
step=args.exports/'Riffle-Rev-G-dressed.step.gz'
dest=args.work/'roundtrip.step'
with gzip.open(step,'rb') as stream,dest.open('wb') as output:shutil.copyfileobj(stream,output)
parts={n.name:n.obj.moved(n.loc) for n in cq.Assembly.load(str(dest)).children}
assert set(['cellDrawing','drawingTail0','drawingTail1','Retainer','bridge','tieS1','tieS2','ph','packplug','Housing'])<=set(parts)
assert not {'cellAlt','Cell','pack0','pack1'}.intersection(parts)
for k in ['Housing','bridge','Retainer']:assert parts[k].isValid() and len(parts[k].Solids())==1
extent=parts['Housing'].BoundingBox().ylen
gap=parts['cellDrawing'].distance(parts['bridge'])
assert abs(extent-74.25)<.001 and abs(gap-.65)<.001
b=parts['packplug'].BoundingBox()
corridor=box(b.xmin-4,b.ymin,b.zmin,b.xlen+4,b.ylen,b.zlen)
# Test the unplug direction against fixed obstacles around the saddle. Leads flex
# and the mated connector itself is omitted; confirm actual disengagement stroke on receipt.
withdraw={k:round(max(0.,corridor.intersect(parts[k]).Volume()),5) for k in ('cellDrawing','Housing','Receiver nut keeper','bridge','drvBoard','batt0','batt1')}
assert all(v<=.002 for v in withdraw.values()),withdraw
with zipfile.ZipFile(args.exports/'Riffle-Rev-G-fit-print.zip') as z:
    checks=[s.split('  ',1) for s in z.read('SHA256SUMS.txt').decode().splitlines()]
    assert all(hashlib.sha256(z.read(n)).hexdigest()==h for h,n in checks)
    stls=[k for k in z.namelist() if k.endswith('.stl')]
    assert len(stls)==14 and sum(k.startswith('Print/') for k in stls)==12
    for k in stls:
        mesh=trimesh.load_mesh(io.BytesIO(z.read(k)),file_type='stl')
        assert mesh.is_volume and mesh.is_watertight and len(mesh.split())==1,k
result=dict(step_sha256=hashlib.sha256(step.read_bytes()).hexdigest(),named_parts=len(parts),housing_extent_y_mm=round(extent,4),max_pack_to_bridge_mm=round(gap,4),ph_withdrawal_4mm_overlap_mm3=withdraw,verified_prints=12,verified_inert_gauges=2,verified_kit_members=len(checks))
(here/'export-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))

