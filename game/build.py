from pathlib import Path
import base64,json
root=Path(__file__).resolve().parent
def image(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
catalog=json.loads((root/'content/catalog.json').read_text(encoding='utf-8'))
catalog['locations']=json.loads((root/'locations.json').read_text(encoding='utf-8'))
template=(root/'src/game.html').read_text(encoding='utf-8')
template=template.replace('</html>', '<!--\n'+(root/'assets/fonts/OFL.txt').read_text(encoding='utf-8')+'\n-->\n</html>')
template=template.replace('</style>',(root/'src/immersive.css').read_text(encoding='utf-8')+'\n</style>',1)
values={'@@SOUND_CHECK@@':'data:audio/wav;base64,'+base64.b64encode((root/'assets/speaker-check.wav').read_bytes()).decode(),'@@FONT@@':base64.b64encode((root/'assets/fonts/AtkinsonHyperlegibleNext.ttf').read_bytes()).decode(),'@@CAD@@':(root/'assets/device-parts.json').read_text(encoding='utf-8-sig'),'@@THREE@@':(root/'assets/device-renderer.min.js').read_text(encoding='utf-8'),'@@SCENES@@':base64.b64encode((root/'assets/landscape.wasm').read_bytes()).decode(),'@@CATALOG@@':json.dumps(catalog),'@@FISH@@':image(root/'assets/fish.png'),'@@WASM@@':base64.b64encode((root/'assets/atlas.wasm').read_bytes()).decode(),'@@DEVICE_UI@@':(root/'src/device-ui.js').read_text(encoding='utf-8').strip()}
for token,filename in [('@@LCD_PICKER@@','lcd-picker.js'),('@@MOBILE_DISPLAY@@','mobile-display.js')]:
 values[token]=(root/'src'/filename).read_text(encoding='utf-8')
for token,value in values.items():
 assert template.count(token)==1,token
 template=template.replace(token,value)
(root/'Thai-Waters-play.html').write_text(template,encoding='utf-8')
