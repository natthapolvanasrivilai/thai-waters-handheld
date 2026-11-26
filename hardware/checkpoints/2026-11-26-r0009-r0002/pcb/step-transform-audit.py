import contextlib,io,re,math
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(__file__.replace('step-transform-audit.py','step-placement-audit.py')).read())
s=step.decode()
entity=dict(re.findall(r'^#(\d+) = (.*?);',s,re.M|re.S))
def links(i): return re.findall(r'#(\d+)',entity[i])
def triple(i): return tuple(map(float,re.search(r"\('',\(([^)]*)\)",entity[i])[1].split(',')))
rr={a[1]:a[0] for a in re.findall(r"^#(\d+) = NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+','([A-Z]+\d+)','',#5,",s,re.M)}
out={}
for row in rows:
    ref=row['reference']
    if ref not in rr: continue
    p, = [i for i,t in entity.items() if t.startswith("PRODUCT_DEFINITION_SHAPE('Placement'") and links(i)==[rr[ref]]]
    relationship, = [links(i)[0] for i,t in entity.items() if t.startswith('CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(') and links(i)[1]==p]
    t, = re.findall(r'WITH_TRANSFORMATION\(#(\d+)\)',entity[relationship])
    origin,dest=links(t)
    assert origin=='11'
    pt, normal, direction=map(triple,links(dest))
    xy_expected=[float(row['pcb_x_mm'])-100,100-float(row['pcb_y_mm'])]
    d=math.dist(pt[:2],xy_expected)
    angle=math.degrees(math.atan2(direction[1],direction[0]))
    err=abs((angle-float(row['pcb_rotation_deg'])+180)%360-180)
    assert d<1e-7 and err<1e-7 and normal==(0,0,1)
    out[ref]={'step_xyz_mm':pt,'pcb_step_xy_error_mm':round(d,12),'angle_error_deg':round(err,12)}
assert len(out)==30
print(json.dumps({'scope':'Native PCB placement compared to registered AP214 root placements (F.Cu; XY export origin KiCad 100,100, Y inverted); no as-built/geometry tolerances','seat_z_mm':sorted({r['step_xyz_mm'][2] for r in out.values()}),'components':out}, indent=2))
