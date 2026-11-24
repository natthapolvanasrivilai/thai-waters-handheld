"""Inspect the delivered native geometry after its print transforms have been applied."""
from zipfile import ZipFile
import json,numpy as np
from color_project import OUT,MODEL,SETTINGS,CORE,PROD,E,value
from interfaces import HERE
from project import read_mesh,manifold
def run():
    with ZipFile(OUT) as z:
        model,cfg=[E.fromstring(z.read(k)) for k in [MODEL,SETTINGS]]
        def native(oid):
            c=model.find(f".//{CORE}object[@id='{oid}']/{CORE}components/{CORE}component")
            return read_mesh(E.fromstring(z.read(c.get(PROD+'path').lstrip('/'))),c.get('objectid'))
        part=cfg.find("object[@id='2']/part")
        s=native(2);s.apply_translation(np.array([float(value(part,'source_offset_'+k)) for k in 'xyz'])-[0,0,3.200001004005232])
        sections=[]
        for x in [-49.99,-49.75,-49.3]:
            loops=[p for p in manifold(s).rotate((0,-90,0)).slice(x).to_polygons() if min(p[:,0])>-15 and max(p[:,0])<-11 and min(p[:,1])>-10 and max(p[:,1])<10]
            assert len(loops)==1,(x,len(loops))
            np.testing.assert_allclose(np.ptp(loops[0],axis=0),[2,2.5],atol=.015)
            sections.append(x)
        bezel=native(4)
        # Bezel is printed outer face down. Cross through its flat front skin.
        loops=manifold(bezel).slice(bezel.bounds[0,2]+.35).to_polygons()
        assert len(loops)==2,len(loops) # one perimeter and the screen opening
        optics=cfg.findall('plate')[3].findall('model_instance'); assert len(optics)==1 and value(optics[0],'object_id')=='28'
        print('Verified output mesh at',sections,'mm: one window, one diffuser; continuous bezel and one screen opening.')
if __name__=='__main__':run()
