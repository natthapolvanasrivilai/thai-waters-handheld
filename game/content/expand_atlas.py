"""Bake the Thai species roster, compact encounter rows, illustration IDs and dietary guilds."""
import argparse,csv,hashlib,json
from pathlib import Path
here=Path(__file__).resolve().parent
fw=here.parents[1]/'firmware/WillowCreek'
def hashed(s):return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4],'little')
locations=json.loads((here.parent/'locations.json').read_text())
legacy_names="""Anabas testudineus|Trichopodus trichopterus|Barbonymus gonionotus|Clarias batrachus|Trichopodus pectoralis|Oreochromis niloticus|Channa striata|Clarias macrocephalus|Oxyeleotris marmorata|Osphronemus goramy|Yasuhikotakia modesta|Barbonymus schwanenfeldii|Mystus multiradiatus|Henicorhynchus siamensis|Barbonymus altus|Hemibagrus wyckioides|Cyclocheilichthys enoplos|Notopterus notopterus|Chitala ornata|Catlocarpio siamensis|Hampala macrolepidota|Desmopuntius johorensis|Channa lucius|Osteochilus vittatus|Barbodes binotatus|Rasbora borapetensis|Channa marulioides|Neolissochilus stracheyi|Channa micropeltes|Tor tambroides|Parambassis siamensis|Pseudomystus siamensis|Hemibagrus nemurus|Labeo chrysophekadion|Cirrhinus microlepis|Crossocheilus oblongus|Pangasianodon hypophthalmus|Wallago attu|Probarbus jullieni|Pangasianodon gigas|Macrobrachium rosenbergii|Urogymnus polylepis|Rastrelliger kanagurta|Selaroides leptolepis|Stolephorus indicus|Rhabdosargus sarba|Selar crumenophthalmus|Scomberoides commersonnianus|Rachycentron canadum|Sphyraena barracuda|Caranx ignobilis|Istiophorus platypterus""".split('|')
aliases={'Himantura polylepis','Puntius binotatus','Puntius gonionotus','Trichogaster trichopterus','Trichogaster pectoralis','Botia modesta','Pangasius hypophthalmus','Osteochilus hasseltii','Cirrhinus siamensis','Labeo siamensis','Sciaena sarba'}
base_diets=[0,0,1,9,0,0,4,3,4,1,9,1,3,1,1,4,1,4,4,1,4,1,4,1,0,2,4,0,4,0,7,3,3,1,1,9,0,4,9,1,3,5,6,7,6,5,7,8,8,8,8,8]
# Design-authored size ranges, bait guild, water, and representative silhouette by family.
groups=[
 ('Cyprinidae Danionidae Xenocyprididae Leuciscidae',2,1,0,8,34),('Cobitidae Nemacheilidae Balitoridae Gastromyzontidae',10,9,0,4,20),
 ('Siluridae Bagridae Sisoridae Pangasiidae Clariidae Akysidae Amblycipitidae',12,3,0,12,65),('Channidae',6,4,0,15,62),
 ('Osphronemidae Anabantidae',1,0,0,5,20),('Notopteridae',18,4,0,19,78),('Mastacembelidae Synbranchidae',60,3,0,15,58),
 ('Ambassidae Adrianichthyidae Aplocheilidae Badidae Nandidae Pristolepididae Cichlidae',30,7,0,3,20),
 ('Gobiidae Oxudercidae Eleotridae Butidae',8,3,4,3,15),('Anguillidae Muraenidae Ophichthidae Congridae',60,5,4,18,95),
 ('Syngnathidae',62,7,4,6,21),('Tetraodontidae Diodontidae',63,5,4,8,29),
 ('Soleidae Cynoglossidae Bothidae Paralichthyidae Psettodidae Samaridae',64,5,4,9,38),
 ('Chaetodontidae Pomacanthidae Ephippidae Zanclidae',65,7,4,7,22),('Serranidae Epinephelidae Lutjanidae Haemulidae Lethrinidae',66,5,4,15,60),
 ('Carcharhinidae Hemiscylliidae Scyliorhinidae Chiloscylliidae Sphyrnidae Stegostomatidae',67,8,4,38,160),
 ('Dasyatidae Myliobatidae Rhinobatidae Mobulidae Rajidae Narcinidae Gymnuridae',41,5,4,20,80),
 ('Labridae Scaridae',68,7,4,8,36),('Pomacentridae',69,7,4,4,18),('Exocoetidae Hemiramphidae Belonidae',70,2,4,9,37),
 ('Scorpaenidae Synanceiidae',71,5,4,7,35),('Ostraciidae Balistidae Monacanthidae',72,7,4,7,30),
 ('Polynemidae',73,5,4,12,56),('Scombridae Istiophoridae Sphyraenidae',74,8,4,24,99),
 ('Callionymidae Blenniidae Platycephalidae Tripterygiidae',75,3,4,5,25),('Engraulidae Clupeidae Dussumieriidae',44,6,4,5,22),
 ('Carangidae',46,8,4,12,58),('Ariidae Plotosidae',15,5,4,12,55),('Apogonidae',30,7,4,3,14)]
family_profiles={family:(art,diet,water,lo,hi) for names,art,diet,water,lo,hi in groups for family in names.split()}
fantasy=[
 ('Reed Lantern Loach',2,0,0,15,9,12,27,'A green light threads the flooded reeds.'),
 ('Cinnabar Glass Barb',3,1,1,15,1,9,23,'Copper scales catch the last light under the ferry.'),
 ('Moonfoil Halfbeak',3,4,96,15,2,16,34,'A silver ribbon slips along the tide line.'),
 ('Lotus Veil Oracle',5,0,0,1,0,30,62,'Its paired eyes shimmer beneath a dawn lotus.'),
 ('Nacre Archfin',5,1,1,2,7,22,47,'The pale fin breaks the current beneath the midday ferry.'),
 ('Karst Mirror Ray',5,2,2,4,5,38,86,'The karst cliffs reflect in its glassy disc at dusk.'),
 ('Mekong Starveil',5,3,3,8,3,50,117,'Two whiskers light the deep channel after nightfall.'),
 ('Andaman Eclipse Sail',5,4,113,4,8,80,151,'Its dark crescent crosses the sinking sun.')]
def mass(cm,art):
    factor=.004 if art in (44,60,62,70) else .022 if art in (41,63,64,69,72) else .013
    return max(1,round(factor*cm**3))
def write_catalog(accepted):
    data=[];diets=list(base_diets)
    for i,(name,tier,pool,spot,mask,diet,low,hi,lore) in enumerate(fantasy):
        assert locations[spot]['pool']==pool,(name,spot,pool)
        art=52+i
        data.append(dict(name=name,tier=tier,site=pool,spot=spot,mask=mask,low=low,high=hi,art=art,diet=diet,form=4 if i==5 else 0,
                         lore=lore,fiction=True,measure='Disc width' if i==5 else 'Total length',reference=mass(hi,41 if i==5 else art)))
    with accepted.open(encoding='utf8') as source:
        records=list(csv.DictReader(source))
    with (here/'thai-field-evidence.csv').open(encoding='utf8') as source:
        supplement=list(csv.DictReader(source))
    field_keys={row['gbif_key'] for row in supplement}
    if len(field_keys)!=len(supplement) or field_keys.intersection(r['gbif_key'] for r in records):
        raise ValueError('Overlapping or duplicate field-evidence species keys')
    records.extend(supplement)
    # Preserve previously assigned IDs on refresh; new records append behind them.
    registry=here/'extended.json'
    past=json.loads(registry.read_text(encoding='utf8')) if registry.exists() else []
    order={r['key']:i for i,r in enumerate(past) if 'key' in r}
    records.sort(key=lambda t:(order.get(int(t['gbif_key']),1000000),t['scientific_name']))
    for r in records:
        name=r['scientific_name'];fam=r['family']
        if name in legacy_names or name in aliases:continue
        seed=hashed(name)
        fallback=(2,0,0,9,35) if r['order'] in ('Cypriniformes','Anabantiformes','Characiformes','Osteoglossiformes') else (43,7,4,9,35)
        art,diet,pool,low,hi=family_profiles.get(fam,fallback)
        if r['gbif_key'] in field_keys:
            if fam in ('Ellopostomatidae','Serpenticobitidae'):art,diet,pool,low,hi=10,9,0,4,20
            if fam in ('Olyridae','Erethistidae'):art,diet,pool,low,hi=12,3,0,4,20
            if fam=='Indostomidae':art,diet,pool,low,hi=62,7,0,2,4
            if fam=='Datnioididae':art,diet,pool,low,hi=30,4,0,12,45
            if name.startswith(('Dermogenys ','Hemirhamphodon ')):art,diet,pool,low,hi=70,2,0,4,13
            if name.startswith('Pao '):art,diet,pool,low,hi=63,5,0,8,29
            if fam in ('Glaucostegidae','Rhinidae'):art,diet,pool,low,hi=67,5,4,38,160
        if fam=='Syngnathidae' and name.startswith('Hippocampus '):art=61
        if pool==0:pool=seed%4
        if name.startswith(('Brachygobius ','Rhinogobius ','Pseudogobiopsis ')):pool=seed%4
        tier=0 if seed%100<37 else 1 if seed%100<70 else 2 if seed%100<90 else 3 if seed%100<98 else 4
        waters=[x['id'] for x in locations if x['pool']==pool]
        spot=waters[(seed>>12)%len(waters)];mask=15 if tier<2 else (1<<((seed>>7)%4))|(1<<((seed>>11)%4))
        # Each new plate has its own identity. The numeric profile describes anatomy.
        data.append(dict(name=name,family=fam,key=int(r['gbif_key']),art=52+len(data),form=4 if art==41 else 2 if art in (12,15,75) else 1 if diet==8 else 0,
                         tier=tier,site=pool,spot=spot,mask=mask,low=low,high=hi,diet=diet,measure='Disc width' if art==41 else 'Total length',reference=mass(hi,art)))
    if len({r['name'] for r in data})!=len(data) or sum(r['tier']==5 for r in data)!=5:
        raise ValueError('Duplicate names or unexpected Mythic count')
    def identity(row):
        return row.get('key') or row['name']
    if list(map(identity,data[:len(past)]))!=list(map(identity,past)):
        raise ValueError('Previously issued species IDs must be preserved')
    registry.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    cpp=[];quote=lambda s:json.dumps(s,ensure_ascii=True)
    for f in data:
        cpp.append('{'+','.join(map(str,[quote(f['name']),f['low'],f['high'],f['tier'],[16,10,6,3,2,1][f['tier']],f['form'],quote(f.get('lore','')),f['site'],f['mask'],f['spot'],f['reference'],quote(f['measure'])]))+'},')
        diets.append(f['diet'])
    (fw/'ExtendedSpecies.h').write_text('// Generated by game/content/expand_atlas.py\n'+'\n'.join(cpp)+'\n')
    (fw/'FishProfiles.h').write_text('#pragma once\n#include <stdint.h>\nnamespace creek {\nconstexpr uint8_t dietForSpecies[]={'+','.join(map(str,diets))+'};\n}\n')
    print(len(data),'additional fish across',len({x['spot'] for x in data}),'host waters')
if __name__=='__main__':
    write_catalog(here/'thai-accepted.csv')
