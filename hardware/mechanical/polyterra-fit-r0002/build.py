"""Rebuild the editable 8-plate project against the verified parent project."""
from receiver import mesh_add
from support_regions import *
def build():
    f=source();r,c=[E.fromstring(f[k]) for k in (MODEL,CFG)];mesh_add(f,r,c)
    for oid,normal in [(2,[-1,0,-1]),(24,[-1,1,0])]:
        o=pose(f,r,c,oid,normal)
        for k,v in {'enable_support':1,'brim_type':'outer_only','brim_width':10,'brim_object_gap':.1}.items():meta(o,k,v)
        tune(o,35)
    edges=json.loads((HERE/'receiver-start-regions.json').read_bytes())
    modifier(f,r,c,2,402,edges,'Local support for raised edges')
    modifier(f,r,c,24,404,[(121,y,5,143,y+6,108) for y in (132,151)],'Two breakaway saddles under palm')
    shell=c.find("object[@id='2']")
    for k,v in dict(support_type='tree(auto)',support_threshold_angle=30,support_top_z_distance=.12,support_object_xy_distance=.23,support_style='tree_hybrid',support_interface_spacing=.1,tree_support_branch_angle=30).items():meta(shell,k,v)
    modifier(f,r,c,2,408,[(87,155,3,111,163,24)],'Power-key opening and outer lip')
    shell.find("part[@id='408']").set('subtype','support_blocker')
    modifier(f,r,c,2,410,[(147,139,34,154,148,57)],'Open rear-face balancing support')
    face_count=shell.find("part[@id='1']/mesh_stat").get('face_count')
    shell.find('metadata[@face_count]').set('face_count',face_count)
    ran=E.Element('objects');ob=E.SubElement(ran,'object',id='1');rg=E.SubElement(ob,'range',min_z='0.2',max_z='96.0')
    E.SubElement(rg,'option',opt_key='layer_height').text='0.12'
    f.update({MODEL:encode(r),CFG:encode(c),'Metadata/layer_config_ranges.xml':encode(ran)})
    write(f,OUT)
if __name__=='__main__':build()
