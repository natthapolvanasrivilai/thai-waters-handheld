from pathlib import Path
import base64,json
root=Path(__file__).resolve().parent
def image(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
catalog=json.loads((root/'content/catalog.json').read_text(encoding='utf-8'))
extended=json.loads((root/'content/extended.json').read_text(encoding='utf-8'))
catalog['fish'].extend(extended)
catalog['ranks'].append('Mythic')
catalog['locations']=json.loads((root/'locations.json').read_text(encoding='utf-8'))
template=(root/'src/game.html').read_text(encoding='utf-8')
template=template.replace('</html>', '<!--\n'+(root/'assets/fonts/OFL.txt').read_text(encoding='utf-8')+'\n-->\n</html>')
template=template.replace('</style>',(root/'src/immersive.css').read_text(encoding='utf-8')+'\n</style>',1)
values={'@@BAIT_ART@@':image(root/'assets/bait.png'),'@@THAI_FONT@@':base64.b64encode((root/'assets/fonts/NotoSansThai.woff2').read_bytes()).decode(),'@@WATER_ART@@':(root/'assets/water-props.json').read_text(encoding='utf-8'),'@@SOUND_CHECK@@':'data:audio/wav;base64,'+base64.b64encode((root/'assets/speaker-check.wav').read_bytes()).decode(),'@@FONT@@':base64.b64encode((root/'assets/fonts/AtkinsonHyperlegibleNext.ttf').read_bytes()).decode(),'@@CAD@@':(root/'assets/device-parts.json').read_text(encoding='utf-8-sig'),'@@THREE@@':(root/'assets/device-renderer.min.js').read_text(encoding='utf-8'),'@@SCENES@@':base64.b64encode((root/'assets/landscape.wasm').read_bytes()).decode(),'@@CATALOG@@':json.dumps(catalog),'@@FISH@@':image(root/'assets/fish.png'),'@@WASM@@':base64.b64encode((root/'assets/atlas.wasm').read_bytes()).decode(),'@@DEVICE_UI@@':(root/'src/device-ui.js').read_text(encoding='utf-8').strip()}
for token,filename in [('@@HANDHELD_INPUT@@','handheld-input.js'),('@@FIELD_GUIDE@@','field-guide.js'),('@@CUP@@','tournament.js'),('@@LCD_PICKER@@','lcd-picker.js'),('@@LCD_RENDERER@@','lcd-renderer.js'),('@@MOBILE_DISPLAY@@','mobile-display.js')]:
 values[token]=(root/'src'/filename).read_text(encoding='utf-8')
values['@@LOCALIZATION@@']=(root/'src/localization.js').read_text(encoding='utf8').replace('@@DICTIONARY@@',json.dumps({**json.loads((root/'src/thai-menu.json').read_text(encoding='utf8')),**json.loads((root/'src/thai-play.json').read_text(encoding='utf8'))},ensure_ascii=False))
for token,file in [('@@LANGUAGE_CONTROL@@','language-control.js'),('@@THAI_ATLAS@@','thai-atlas.js')]:
 values[token]=(root/'src'/file).read_text(encoding='utf8')
# The standalone page embeds the atlas module in its classic game script.
values['@@THAI_ATLAS@@']=values['@@THAI_ATLAS@@'].replace('export function thaiAtlas(', 'function thaiAtlas(')
template=template.replace('</html>', '<!-- Noto Sans Thai: '+(root/'assets/fonts/NotoSansThai-OFL.txt').read_text(encoding='utf8')+' -->\n</html>')
for face in ('SyyUDT-Regular','SyyUDS-Regular','SyyFlowey-Bold'):
 values['@@'+face+'@@']=base64.b64encode((root/'assets/fonts'/(face+'.woff2')).read_bytes()).decode()
template=template.replace('</html>', '<!-- '+(root/'assets/fonts/Syy-OFL.txt').read_text(encoding='utf8')+' -->\n</html>')
for token,value in values.items():
 assert template.count(token)==1,token
 template=template.replace(token,value)
(root/'Thai-Waters-play.html').write_text(template,encoding='utf-8')
