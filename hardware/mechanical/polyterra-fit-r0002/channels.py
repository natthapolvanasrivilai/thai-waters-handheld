"""Measure deposited polymer inside the service openings in the 45-degree frame."""
from kit import *
from shapely.geometry import MultiPoint,box
sys.path.insert(0,str(BASE.parent/'TW-A-0001-R0014/Printing'))
from rail_paths import footprints
def verify(gcode):
    rot=trimesh.geometry.align_vectors(np.array([-1,0,-1])/np.sqrt(2),[0,0,-1])
    f=source();m=read(f,E.fromstring(f[MODEL]),2)[0];m.apply_transform(rot)
    shift=np.array([128,126,0])-np.r_[m.bounds.mean(0)[:2],m.bounds[0,2]]
    def cyl(x,y,r,z0,z1):
        a=trimesh.creation.cylinder(radius=r,height=z1-z0,sections=32)
        a.apply_translation([x,y,(z0+z1)/2]);return a
    def cub(x,y,zz,X,Y,Z):return trimesh.creation.box(bounds=[[x,y,zz],[X,Y,Z]])
    cases=[('status aperture',cub(-49.9,-1.05,12.4,-44.25,1.05,13.8)),('key',cub(-37.5,33.65,11.4,-34.5,33.9,13.7))]
    for y in (-24,24):
        cases.extend([(f'driver {y}',cyl(51,y,2.02,.6,22.35)),(f'shank {y}',cyl(51,y,1,22.85,25.5))])
    for x in (-36,36):
        for y in (-24.25,24.25):cases.append((f'controller {x} {y}',cyl(x,y,2.02,.6,9)))
    for y in (-18,18):cases.append((f'hook {y}',cub(-47.84,y-1.5,24.9,-46.9,y+1.5,27.5)))
    height={};h=.2;z=0;role=None;visible=False
    for line in gcode.open():
        if line.startswith('; Z_HEIGHT:'):z=float(line.split(':')[-1]);visible=False
        elif line.startswith('; LAYER_HEIGHT:'):h=float(line.split(':')[-1])
        elif line.startswith(('; OBJECT_ID:', '; start printing object, unique label id:')):visible=line.split(':')[-1].strip()=='385'
        elif line.startswith('; stop printing object'):visible=False
        elif line.startswith('; FEATURE:'):role=line.split(':')[-1].strip()
        elif visible and line.startswith(('G1 ','G2 ','G3 ')) and ' E' in line:
            kind='support' if role and role.startswith('Support') else 'model'
            height[z,kind]=max(height.get((z,kind),0),h)
    results=[]
    for name,w in cases:
        w.apply_translation([-3.140001297,-2.575000763,-12.3000009]);w.apply_transform(rot);w.apply_translation(shift)
        a,b=w.bounds
        paths=footprints(gcode,box(a[0]-2,a[1]-2,b[0]+2,b[1]+2),a[2],b[2]+.20)
        mx={'model':0,'support':0};nr=nm=0
        for z,p in paths.items():
            for k in p:
                # Check the swept bead near both surfaces and at the layer midpoint.
                for frac in (.01,.5,.99):
                    plane=z-frac*height.get((z,k),.12)
                    if not a[2]<plane<b[2]:continue
                    edges=trimesh.intersections.mesh_plane(w,[0,0,1],[0,0,plane])
                    if len(edges):
                        region=MultiPoint(edges[:,:,:2].reshape(-1,2)).convex_hull
                        mx[k]=max(mx[k],region.intersection(p[k]).area)
            nm+=int('model' in p);nr+=1
        results.append(dict(feature=name,layers=nr,rim_model_layers=nm,max_mm2={k:round(v,4) for k,v in mx.items()}))
        print(results[-1],flush=True)
    return results
if __name__=='__main__':
    result=verify(Path(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(result,indent=2))

    assert len(result)==12 and all(row["rim_model_layers"]>0 and max(row["max_mm2"].values())<.001 for row in result),result
