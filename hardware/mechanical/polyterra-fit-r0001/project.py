"""Make the all-PLA process variant from the immutable R0004 geometry."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
import json
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'enclosure-print-r0004'
SOURCE = next(BASE.glob('*.3mf'))
OUT = HERE / 'Thai-Waters-R0004-PolyTerra-PLA-SuperTack-X1C.3mf'
PLATE = 'Supertack Plate'
MODEL_SETTINGS = 'Metadata/model_settings.config'
PROJECT_SETTINGS = 'Metadata/project_settings.config'
PLATES = ['Sage housing and status shelf', 'Charcoal bezel and reel', 'Sage rod handle',
          'White diffuser fit gauge', 'Black mask and cover fit gauges', 'Gray battery gauges',
          'Gray PCB and component gauges', 'Amber reel controls and power cap']
PROFILE = 'PolyTerra PLA @BBL X1C'

def read_profile(folder, name):
    raw = json.loads((folder / (name + '.json')).read_bytes())
    profile = read_profile(folder,raw['inherits']) if 'inherits' in raw else {}
    for include in raw.get('include', []):
        profile.update(read_profile(folder, include))
    profile.update(raw)
    return profile

def meta(node, key, val):
    child = node.find(f"metadata[@key='{key}']")
    if child is None:
        child = ET.SubElement(node, 'metadata', key=key)
    child.set('value', val)

def build(folder):
    assert sha256(SOURCE.read_bytes()).hexdigest()=='084176b7ff1e857d779bcacd9940d1a35a510e32d9cf77b1b559c2b1525c1890'
    with ZipFile(SOURCE) as z:
        files = {k:z.read(k) for k in z.namelist()}
    p = json.loads(files[PROJECT_SETTINGS])
    stock = read_profile(folder, PROFILE)
    assert stock['filament_type']==['PLA'] and stock['nozzle_temperature'][0]=='220'
    # All six color slots use the X1C standard-flow hot end. The source keeps
    # machine and process variants as separate vectors; change filament keys only.
    for k,v in stock.items():
        if k in p and isinstance(v,list) and k not in ('compatible_printers','include','filament_colour'):
            if k in ('long_retractions_when_ec','retraction_distances_when_ec'):
                p[k]=[v[0]]*len(p[k])
            elif isinstance(p[k],list) and len(p[k])==6:
                p[k]=[v[0]]*6
    p.update(filament_settings_id=[PROFILE]*6, filament_ids=[stock['filament_id']]*6,
             filament_extruder_variant=['Direct Drive Standard']*6,
             filament_max_volumetric_speed=['12']*6, curr_bed_type=PLATE)
    p['filament_colour'][3]='#EEEDE8'
    p['outer_wall_speed']=['55']*len(p['outer_wall_speed'])
    p['top_surface_speed']=['45']*len(p['top_surface_speed'])
    p['initial_layer_speed']=['25']*len(p['initial_layer_speed'])
    cfg=ET.fromstring(files[MODEL_SETTINGS])
    from support import block_channels
    block_channels(files,cfg)
    for i,plate in enumerate(cfg.findall('plate')):
        meta(plate,'bed_type',PLATE)
        meta(plate,'plater_name',f'{i+1:02d} PLA - {PLATES[i]}')
    for oid in (16,18,28,32,114):
        obj=cfg.find(f"object[@id='{oid}']")
        meta(obj,'layer_height','0.12')
        meta(obj,'wall_generator','arachne')
    for oid in (28,38):
        meta(cfg.find(f"object[@id='{oid}']"),'brim_type','no_brim')
    for oid,title in {28:'Diffuser - opaque PLA fit gauge',32:'USB mask - rigid PLA fit gauge',
                      34:'Service cover - rigid PLA fit gauge'}.items():
        obj=cfg.find(f"object[@id='{oid}']")
        meta(obj,'name',title)
        meta(obj.find('part'), 'name',title)
    files[MODEL_SETTINGS]=ET.tostring(cfg,encoding='utf-8',xml_declaration=True)
    files[PROJECT_SETTINGS]=json.dumps(p,ensure_ascii=False,indent=2).encode()
    with ZipFile(OUT,'w') as z:
        for k,v in sorted(files.items()):
            z.writestr(ZipInfo(k,(2026,11,24,0,0,0)),v,compress_type=ZIP_DEFLATED)
if __name__=='__main__':
    import sys
    build(Path(sys.argv[1]))
