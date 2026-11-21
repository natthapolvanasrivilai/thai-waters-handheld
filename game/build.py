from pathlib import Path
import base64,hashlib,json,re,unicodedata
root=Path(__file__).resolve().parent
def image(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
catalog=json.loads((root/'content/catalog.json').read_text(encoding='utf-8'))
extended=json.loads((root/'content/extended.json').read_text(encoding='utf-8'))
catalog['fish'].extend(extended)
catalog['ranks'].append('Mythic')
catalog['locations']=json.loads((root/'locations.json').read_text(encoding='utf-8'))
template=(root/'src/game.html').read_text(encoding='utf-8')

hq=json.loads((root/'assets/fish-hq-pilot.json').read_text(encoding='utf-8'))
assert hq['format']=='thai-waters-fish-hq/v1' and (hq['width'],hq['height'])==(288,150)
assert set(hq['portraits'])=={'1822','2158','2160','2190','2192'}
field_dir=root/'art-source/field'
manifest=json.loads((field_dir/'plates.json').read_text(encoding='utf-8'))
def verify_art_file(name,expected):
 assert Path(name).name==name and name.endswith('.png'),name
 assert hashlib.sha256((field_dir/name).read_bytes()).hexdigest()==expected,name
hq_images={}
hq_bytes=0
for key,r in hq['portraits'].items():
 id=int(key)
 stable=[tile for tile in manifest if id in tile['ids']]
 assert str(r['id'])==key and len(stable)==1,key
 tile=stable[0]
 idx=tile['ids'].index(id)
 assert r['scientific']==tile['species'][idx]==catalog['fish'][id]['name'],key
 rep=tile.get('replacements',{}).get(key)
 assert rep==r['replacement'],key
 expected=rep if rep else tile
 assert r['file']==expected['file'] and r['source_sha256']==expected['sha256'],key
 assert r['cell']==(rep.get('cell',1) if rep else idx+1),key
 verify_art_file(tile['file'],tile['sha256'])
 if rep:
  verify_art_file(rep['file'],rep['sha256'])
  if rep.get('reference'):verify_art_file(rep['reference'],rep['reference_sha256'])
 assert all(0<b<=a for a,b in zip(r['source_dimensions'],r['art_dimensions'])),key
 data=base64.b64decode(r['webp'],validate=True)
 assert data[:4]==b'RIFF' and data[8:12]==b'WEBP' and 3000<=len(data)<=30000,key
 assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],key
 hq_bytes+=len(data)
 hq_images[key]={'scientific':r['scientific'],'webp':r['webp']}
assert hq_bytes<=80000
hq_js=(root/'src/hq-portraits.js').read_text(encoding='utf-8')
assert hq_js.count('@@HQ_WEBP@@')==1
hq_js=hq_js.replace('@@HQ_WEBP@@',json.dumps(hq_images,separators=(',',':')))
template=template.replace('</html>', '<!--\n'+(root/'assets/fonts/OFL.txt').read_text(encoding='utf-8')+'\n-->\n</html>')
template=template.replace('</style>',(root/'src/immersive.css').read_text(encoding='utf-8')+'\n</style>',1)
values={'@@SALVAGE_DATA@@':(root/'content/salvage.json').read_text(encoding='utf8'),'@@SALVAGE_ART@@':image(root/'assets/salvage.png'),'@@BAIT_ART@@':image(root/'assets/bait.png'),'@@THAI_FONT@@':base64.b64encode((root/'assets/fonts/NotoSansThai.woff2').read_bytes()).decode(),'@@WATER_ART@@':(root/'assets/water-props.json').read_text(encoding='utf-8'),'@@SOUND_CHECK@@':'data:audio/wav;base64,'+base64.b64encode((root/'assets/speaker-check.wav').read_bytes()).decode(),'@@FONT@@':base64.b64encode((root/'assets/fonts/AtkinsonHyperlegibleNext.ttf').read_bytes()).decode(),'@@CAD@@':(root/'assets/device-parts.json').read_text(encoding='utf-8-sig'),'@@THREE@@':(root/'assets/device-renderer.min.js').read_text(encoding='utf-8'),'@@SCENES@@':base64.b64encode((root/'assets/landscape.wasm').read_bytes()).decode(),'@@CATALOG@@':json.dumps(catalog),'@@FISH@@':image(root/'assets/fish.png'),'@@WASM@@':base64.b64encode((root/'assets/atlas.wasm').read_bytes()).decode(),'@@DEVICE_UI@@':(root/'src/device-ui.js').read_text(encoding='utf-8').strip()}
for token,filename in [('@@HANDHELD_INPUT@@','handheld-input.js'),('@@CAREER_STORAGE@@','career-storage.js'),('@@FIELD_GUIDE@@','field-guide.js'),('@@CUP@@','tournament.js'),('@@LCD_PICKER@@','lcd-picker.js'),('@@MENU_SHEETS@@','menu-sheets.js'),('@@LCD_RENDERER@@','lcd-renderer.js'),('@@MOBILE_DISPLAY@@','mobile-display.js')]:
 values[token]=(root/'src'/filename).read_text(encoding='utf-8')
values['@@LOCALIZATION@@']=(root/'src/localization.js').read_text(encoding='utf8').replace('@@DICTIONARY@@',json.dumps({**json.loads((root/'src/thai-menu.json').read_text(encoding='utf8')),**json.loads((root/'src/thai-play.json').read_text(encoding='utf8'))},ensure_ascii=False))
for token,file in [('@@LANGUAGE_CONTROL@@','language-control.js'),('@@THAI_ATLAS@@','thai-atlas.js')]:
 values[token]=(root/'src'/file).read_text(encoding='utf8')
thai_names=json.loads((root/'content/thai-specimen-labels.json').read_text(encoding='utf8'))
thai_name_import="import thaiSpecimenLabels from '../content/thai-specimen-labels.json' with { type: 'json' };"
assert values['@@THAI_ATLAS@@'].count(thai_name_import)==1
thai_names_literal=json.dumps(thai_names,ensure_ascii=False)
assert '</script' not in thai_names_literal.lower()
values['@@THAI_ATLAS@@']=values['@@THAI_ATLAS@@'].replace(thai_name_import,'const thaiSpecimenLabels = '+thai_names_literal+';')
transcriptions=json.loads((root/'content/thai-scientific-transcriptions.json').read_text(encoding='utf8'))
assert transcriptions['format']=='pocket-reel-thai-scientific-transcriptions/v1'
keyed=[f['name'] for f in catalog['fish'] if f.get('key')]
assert len(keyed)==len(set(keyed)), 'duplicate keyed Latin identity'
assert set(transcriptions['names'])==set(keyed), 'scientific transcription keys must exactly cover the keyed catalog'
for exact, label in transcriptions['names'].items():
 assert label==unicodedata.normalize('NFC',label) and re.fullmatch(r'[ก-๙]+(?:[ -][ก-๙]+)*',label), exact
transcript_import="import thaiSpecimenTranscriptions from '../content/thai-scientific-transcriptions.json' with { type: 'json' };"
assert values['@@THAI_ATLAS@@'].count(transcript_import)==1
transcript_literal=json.dumps(transcriptions,ensure_ascii=False,separators=(',',':'))
assert '</script' not in transcript_literal.lower()
values['@@THAI_ATLAS@@']=values['@@THAI_ATLAS@@'].replace(transcript_import,'const thaiSpecimenTranscriptions = '+transcript_literal+';')
# The standalone page embeds the atlas module in its classic game script.
values['@@THAI_ATLAS@@']=values['@@THAI_ATLAS@@'].replace('export function thaiAtlas(', 'function thaiAtlas(')
template=template.replace('</html>', '<!-- Noto Sans Thai: '+(root/'assets/fonts/NotoSansThai-OFL.txt').read_text(encoding='utf8')+' -->\n</html>')
for face in ('SyyUDT-Regular','SyyUDS-Regular','SyyFlowey-Bold'):
 values['@@'+face+'@@']=base64.b64encode((root/'assets/fonts'/(face+'.woff2')).read_bytes()).decode()
template=template.replace('</html>', '<!-- '+(root/'assets/fonts/Syy-OFL.txt').read_text(encoding='utf8')+' -->\n</html>')
credits=['thai-specimen-labels.md','field-evidence.md','thai-field-datasets.csv','thai-field-evidence.csv','specimen-image-credits.csv']
field_bank=(root/'assets/TW-FISH.BIN').read_bytes()
values['@@FIELD_BANK@@']=base64.b64encode(field_bank).decode()
values['@@BANK_SHA@@']=hashlib.sha256(field_bank).hexdigest()
values['@@FISH_CREDITS@@']=base64.b64encode(('\n\n'.join(name+'\n'+(root/'content'/name).read_text(encoding='utf8') for name in credits)).encode()).decode()
values['@@UI_AUDIO@@']=(root/'src/ui-audio.js').read_text(encoding='utf8')
values['@@HQ_PORTRAITS@@']=hq_js
for token,value in values.items():
 assert template.count(token)==1,token
 template=template.replace(token,value)
(root/'Thai-Waters-play.html').write_text(template,encoding='utf-8')
