"""Check the supplier service motion against the fixed installed geometry (mm)."""
import argparse
import csv
from pathlib import Path
import sys
from math import radians
import numpy as np
import cadquery as cq
import fcl
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from build import HERE, OLD, digest, load, save

HARNESS = HERE.parents[1]/"electronics/harness-r0005"
sys.path.insert(0,str(HARNESS))
from mate import loop_edge, arc_length, actuate, split_latch, guide, jacket, STROKE, RELEASE_DEG, JACKET_OD

def tri(shape):
    v,t=shape.tessellate(.025,.10)
    return np.array([p.toTuple() for p in v]),np.array(t)

BOXES={}
def model(v,t):
    b=fcl.BVHModel()
    b.beginModel(len(v),len(t))
    b.addSubModel(v,t)
    b.endModel()
    m=fcl.CollisionObject(b)
    BOXES[id(m)]=np.stack([np.min(v,axis=0),np.max(v,axis=0)])
    return m

def meshgap(a,b):
    r=fcl.DistanceResult()
    d=fcl.distance(a,b,fcl.DistanceRequest(enable_nearest_points=True),r)
    return max(0.,d)

def native_gap(a,b):
    tool=BRepExtrema_DistShapeShape(a.wrapped,b.wrapped)
    if not tool.IsDone():raise ValueError("Native distance failed")
    def coord(p):return [round(p.X(),5),round(p.Y(),5),round(p.Z(),5)]
    return dict(gap_mm=round(tool.Value(),6),moving_xyz_mm=coord(tool.PointOnShape1(1)),fixed_xyz_mm=coord(tool.PointOnShape2(1)))

def tube(points,radius):
    p=np.array(points)
    tangent=np.gradient(p,axis=0)
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    u=np.cross(tangent,[0,0,1])
    u/=np.linalg.norm(u,axis=1)[:,None]
    v=np.cross(tangent,u)
    ring=np.arange(24)*2*np.pi/24
    verts=(p[:,None,:]+radius*(np.cos(ring)[None,:,None]*u[:,None,:]+np.sin(ring)[None,:,None]*v[:,None,:])).reshape(-1,3)
    faces=[]
    for i in range(len(p)-1):
        for j in range(24):
            a=24*i+j;b=24*i+(j+1)%24
            faces.extend(((a,b,a+24),(b,b+24,a+24)))
    for j in range(1,23):
        faces.extend(((0,j,j+1),((len(p)-1)*24,(len(p)-1)*24+j+1,(len(p)-1)*24+j)))
    return model(verts,np.array(faces))

def read_shapes(cache):
    changes=load(HARNESS/'installed.json')
    old=load(OLD/'installed-step.json')['components']
    paths={k:cache/(k+'.brep') for k in old if k not in changes['remove']}
    paths.update({r['name']:HARNESS/r['brep'] for r in changes['add']})
    return {k:cq.Shape.importBrep(str(p)) for k,p in paths.items()}

def run(cache):
    ss=read_shapes(cache)
    print("Loaded native assembly nodes",flush=True)
    plug=ss['A3-J1-plug']; header=ss['A3-J1-header']
    body,latch=split_latch(plug)
    assert abs(plug.Volume()-body.Volume()-latch.Volume())<.0005
    rigid_ids=[k for k in ss if k.startswith('A3-J1-C') or k.startswith('wh') and k.endswith('-Cu')]+['A3-J1-TPA']
    rigid0=cq.Compound.makeCompound([body,*[ss[k] for k in rigid_ids]])
    wire_ids=sorted(k for k in ss if k.startswith(('w1','tee-','termination-W1-')) or k=='J8plug')
    loom=cq.Compound.makeCompound([ss[k] for k in wire_ids])
    # After disconnecting the display, move the A1/A4/A5 assembly clear while
    # retaining J8/W1 at its exact installed pose in an independent support.
    excluded={k for k in ss if k.startswith(('A1-','A4-','A5-','USB-'))} | {'Bezel','statusPwrGuide','statusChgGuide','statusUsbGuide'}
    moving=set(rigid_ids)|{'A3-J1-plug'}|{k for k in ss if k.startswith('wh')}
    land=header.Solids()[0]
    overlap=plug.intersect(land)
    locked=[dict(volume_mm3=round(s.Volume(),6),center_mm=[round(v,5) for v in s.Center().toTuple()]) for s in overlap.Solids()]
    body_released=cq.Compound.makeCompound([rigid0,actuate(latch,1)])
    routes=load(HARNESS/'routing.json')
    # Keep all parts whose AABBs reach the service zone. Other installed
    # parts cannot be distance minimizers inside this enlarged coordinate box.
    objects={}
    for k,s in ss.items():
        if k in moving:continue
        b=s.BoundingBox()
        if b.xmax<2 or b.xmin>43 or b.ymax<-21 or b.ymin>31 or b.zmax<2 or b.zmin>24:continue
        meshfile=cache.parent/'mesh'/(k+'.npz')
        if meshfile.exists() and not (HARNESS/'placed'/(k+'.brep')).exists():
            with np.load(meshfile) as f:objects[k]=model(f['v'],f['i'])
        else: objects[k]=model(*tri(s))
    print("Fixed meshes ready",flush=True)
    rb=model(*tri(rigid0)); rigid_latch={}; rows=[]; candidates={}
    # Treat the shroud mating pair separately from unrelated external objects.
    closed=[k for k in objects if k!='A3-J1-header']
    fixed=[k for k in closed if k not in excluded]
    def best(m,keys):
        box=BOXES[id(m)]+m.getTranslation()
        candidates=[]
        for k in keys:
            other=BOXES[id(objects[k])]
            gap=np.linalg.norm(np.maximum(0,np.maximum(box[0]-other[1],other[0]-box[1])))
            candidates.append((gap,k))
        best_value=float('inf');best_name=''
        for lower,k in sorted(candidates):
            if lower>best_value+.00001:break
            key=(id(m),k)
            if key not in memo:memo[key]=meshgap(m,objects[k])
            if memo[key]<best_value:best_value,best_name=memo[key],k
        return best_value,best_name
    for idx in range(9+67):
        memo={}
        phase='press' if idx<9 else 'withdraw'
        u=idx/8 if idx<9 else 1
        d=0. if idx<9 else (idx-9)*.125
        if u not in rigid_latch:rigid_latch[u]=model(*tri(actuate(latch,u)))
        rl=rigid_latch[u]
        for m in [rb,rl]:m.setTranslation(np.array([0.,d,0.]))
        closest=min(best(m,wire_ids) for m in [rb,rl])
        external=min(best(m,fixed) for m in [rb,rl])
        closed_gap=min(best(m,closed) for m in [rb,rl])
        lead_min=(999.,'',''); branch_w1=(999.,'',''); installed_lead=(999.,'','')
        leads={}
        for net in ['VCC','SCL','SDA','GND']:
            tx,_,z=routes[net]['tap_center_mm']
            pts=guide(net,tx,z,d)
            pts.insert(0,[pts[0][0],-5.35+d,10.36])
            m=tube(pts,JACKET_OD/2); leads[net]=m
            # The participating net joins its own tee. Distance to its own
            # jacket outside the splice and all other nets is still checked.
            others=[k for k in fixed if not k.startswith('tee-'+net+'-')]
            lead_min=min(lead_min,(*best(m,others),net))
            installed_lead=min(installed_lead,(*best(m,[k for k in closed if not k.startswith('tee-'+net+'-')]),net))
            branch_w1=min(branch_w1,(*best(m,[k for k in wire_ids if k in others]),net))
        for net,m in leads.items():
            for n,b in leads.items():
                if n<net:lead_min=min(lead_min,(meshgap(m,b),'wh'+n,net))
        row=dict(phase=phase,press_fraction=u,travel_mm=round(d,3),rigid_W1_mesh_mm=round(closest[0],5),rigid_W1_part=closest[1],
                 installed_rigid_mesh_mm=round(closed_gap[0],5),installed_part=closed_gap[1],other_rigid_mesh_mm=round(external[0],5),external_part=external[1],W4_mesh_mm=round(lead_min[0],5),W4_net=lead_min[2],W4_part=lead_min[1],
                 installed_W4_mesh_mm=round(installed_lead[0],5),installed_W4_net=installed_lead[2],installed_W4_part=installed_lead[1],W4_W1_mesh_mm=round(branch_w1[0],5),W4_W1_net=branch_w1[2],W4_W1_part=branch_w1[1])
        rows.append(row)
        if idx%10==0: print(idx,row,flush=True)
    # Native OCC extrema over the entire translated compound and fixed W1.
    # Rigid translation is 1-Lipschitz. Rotation varies no faster than r*dθ.
    print("Mesh path complete",flush=True)
    distances=[]
    for row in rows:
        u,d=row['press_fraction'],row['travel_mm']
        a=(body_released if u==1 else cq.Compound.makeCompound([rigid0,actuate(latch,u)])).translate((0,d,0))
        bounds=a.BoundingBox()
        def lower(k):
            b=ss[k].BoundingBox()
            return sum(max(0,getattr(bounds,c+'min')-getattr(b,c+'max'),getattr(b,c+'min')-getattr(bounds,c+'max'))**2 for c in 'xyz')**.5
        key=row['rigid_W1_part']; res=native_gap(a,ss[key])
        for k in wire_ids:
            if k!=key and lower(k)<res['gap_mm']+.00002:
                candidate=native_gap(a,ss[k])
                if candidate['gap_mm']<res['gap_mm']:key,res=k,candidate
        row.update(rigid_W1_native_mm=res['gap_mm'],native_part=key)
        if len(distances)%10==0:print('Native station',len(distances),res,flush=True)
        distances.append(dict(**res,phase=row['phase'],press_fraction=u,travel_mm=d,part=key))
    winner=min(distances,key=lambda r:r['gap_mm'])
    # Maximum point radius from the rotation axis; every locus is bounded.
    verts,_=tri(latch)
    radius=max(np.hypot(verts[:,1]+6.55,verts[:,2]-13.56))
    bound=max(.125/2,radius*abs(radians(RELEASE_DEG))/16)+.00001
    jaw=actuate(latch,1)
    latch_released=native_gap(jaw,land)
    foreign=min(rows,key=lambda r:r['other_rigid_mesh_mm'])
    flex=min(rows,key=lambda r:r['W4_mesh_mm'])
    flex_loom=min(rows,key=lambda r:r['W4_W1_mesh_mm'])
    net=flex['W4_net'];tx,_,z=routes[net]['tap_center_mm']
    offending,ln=jacket(net,tx,z,flex['travel_mm'])
    part=flex['W4_part']
    if part.startswith('wh'):
        n=part[2:]; xx,_,zz=routes[n]['tap_center_mm']; obs=jacket(n,xx,zz,flex['travel_mm'])[0]
    else:obs=ss[part]
    result=dict(units='mm',revision=HERE.name,reported_state='engineering study; physical release unverified',
        rigid_members=['A3-J1-plug (body and rocker)',*rigid_ids],W1_stationary_members=wire_ids,
        lifted_display_members=sorted(excluded),service_background_mesh_members=sorted(objects),
        stroke_mm=STROKE,rocker_pivot_xyz_mm=[20.96,-6.55,13.56],rocker_angle_deg=RELEASE_DEG,
        unmodified_seated_plastics_intersections=locked,unmodified_pin_to_plug_overlap_mm3=round(sum(plug.intersect(p).Volume() for p in header.Solids()[1:]),6),
        released_rocker_to_shroud=latch_released,plug_to_TPA_overlap_mm3=round(plug.intersect(ss['A3-J1-TPA']).Volume(),5),
        rigid_W1_minimum_sample=winner,continuous_rigid_W1_lower_bound_mm=round(max(0,winner['gap_mm']-bound),5),sampling_allowance_mm=round(bound,6),
        manufacturing_sensitivity_mm={'header_registration':.2,'housing_width':.2,'W1_dress_fixture_assumed':.5,'sum_worst_case':.9},
        after_illustrative_stack_lower_bound_mm=round(winner['gap_mm']-bound-.9,5),minimum_installed_rigid_mesh=min(rows,key=lambda r:r['installed_rigid_mesh_mm']),minimum_other_rigid_mesh=foreign,minimum_W4_mesh=flex,
        minimum_installed_W4_mesh=min(rows,key=lambda r:r['installed_W4_mesh_mm']),minimum_W4_to_stationary_loom_mesh=flex_loom,offending_W4_native=dict(**native_gap(offending,obs),intersection_mm3=round(offending.intersect(obs).Volume(),5)),
        full_stroke_to_header=native_gap(body_released.translate((0,STROKE,0)),header),
        released_rocker_to_plug_body_overlap_mm3=round(jaw.intersect(body).Volume(),5),
        terminal_to_capped_plug_overlap_mm3={k:round(ss[k].intersect(plug).Volume(),5) for k in rigid_ids if k.startswith('A3-J1-C')},
        seated_TPA_to_wires_mm={k:round(ss['A3-J1-TPA'].distance(ss[k]),5) for k in ss if k.startswith('wh') and not k.endswith('-Cu')},
        header_tail_overlap_by_pin_mm3={str(i+1):round(p.intersect(ss['drvBoard']).Volume(),6) for i,p in enumerate(sorted(header.Solids()[1:],key=lambda p:p.Center().x))},
        board_to_header_plastic_mm=round(land.distance(ss['drvParts']),5),
        header_tails_to_A3_substrate_mm3=round(header.intersect(ss['drvBoard']).Volume(),5),
        source_hashes={r['name']:r['sha256'] for r in load(HARNESS/'installed.json')['add']},
        report='Mesh screening of flex and surroundings is sampled. Only the rigid-to-W1 minimum has a continuous native distance bound. Receiver underside and inner terminal cavities are incomplete in the supplier CAD.')
    # Native splines for all 67 service stations are reconstructed from the
    # common constant-length guide, with independent checks on bend radius.
    route_evidence={}
    for net in ['VCC','SCL','SDA','GND']:
        xx,_,zz=routes[net]['tap_center_mm']
        lengths=[];radii=[];peak=0
        for d in np.linspace(0,STROKE,67):
            pts=guide(net,xx,zz,d,97)
            edge=loop_edge(net,xx,zz,d)
            lengths.append(3.95+arc_length(edge))
            radii.append(1/max(edge.curvatureAt(t) for t in np.linspace(0,1,121)))
            peak=max(peak,max(p[2] for p in pts)+JACKET_OD/2)
        route_evidence[net]=dict(min_centerline_radius_mm=round(min(radii),4),radius_at_travel_mm=round(.125*int(np.argmin(radii)),4),length_mm=[round(min(lengths),5),round(max(lengths),5)],max_jacket_Z_mm=round(peak,3))
    result['W4_geometry']=route_evidence
    save(HARNESS/'clearance.json',result)
    with (HERE/'QA/service-path.csv').open('w',newline='') as f:
        out=csv.DictWriter(f,fieldnames=rows[0]);out.writeheader();out.writerows(rows)
    print('Result',winner,flex,foreign,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-breps',type=Path,required=True,help='R0011 STEP children exported in installed coordinates')
    run(p.parse_args().baseline_breps)
