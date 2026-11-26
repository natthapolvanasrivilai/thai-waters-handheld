"""Keep breakaway supports out of narrow service passages in the R0004 housing."""
from copy import deepcopy
from lxml import etree as E

HOUSING='3D/Objects/object_1.model'
BOUNDS=[(-52.5,-3.10,10.70,-41.60,3.10,26.8)]
BOUNDS += [(51-2.65,y-2.65,-3.35,51+2.65,y+2.65,26.10) for y in (-24,24)]
BOUNDS += [(x-2.65,y-2.65,-3.35,x+2.65,y+2.65,20.0) for x in (-36,36) for y in (-24.25,24.25)]
# Bambu boolean support-blocker shells. The deposited device solid is untouched.
TRIS=[(0,2,1),(1,2,3),(4,5,6),(5,7,6),(0,4,2),(4,6,2),
      (1,3,5),(3,7,5),(0,1,4),(1,5,4),(2,6,3),(3,6,7)]
def block_channels(files,cfg):
    xml=E.fromstring(files[HOUSING])
    part=cfg.find("object[@id='2']/part[@id='1']")
    offsets=[float(part.find(f"metadata[@key='source_offset_{k}']").get('value')) for k in 'xyz']
    offset=[-offsets[0],-offsets[1],3.200001004005232-offsets[2]]
    m=xml.find(".//{*}object[@id='301']/{*}mesh")
    v,f=m.find('{*}vertices'),m.find('{*}triangles')
    for bounds in BOUNDS:
        start=len(v)
        for z in (bounds[2],bounds[5]):
            for y in (bounds[1],bounds[4]):
                for x in (bounds[0],bounds[3]):
                    n=deepcopy(v[0])
                    for k,val,delta in zip('xyz',(x,y,z),offset):n.set(k,f'{val+delta:.8f}')
                    v.append(n)
        for tri in TRIS:
            n=deepcopy(f[0])
            for k,i in zip(('v1','v2','v3'),tri):n.set(k,str(i+start))
            f.append(n)
    files[HOUSING]=E.tostring(xml,encoding='UTF-8',xml_declaration=True)
    cfg.find("object[@id='2']/part[@id='301']/metadata[@key='name']").set('value','Support exclusions - USB entry, status channel and rear driver passages')
