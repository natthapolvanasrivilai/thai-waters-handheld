from pathlib import Path
import base64,json
root=Path(__file__).resolve().parent
def image(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
catalog=json.loads((root/'content/catalog.json').read_text(encoding='utf-8'))
catalog['locations']=json.loads((root/'locations.json').read_text(encoding='utf-8'))
template=(root/'src/game.html').read_text(encoding='utf-8')
values={'@@CAD@@':(root/'assets/device-parts.json').read_text(encoding='utf-8-sig'),'@@THREE@@':(root/'assets/device-renderer.min.js').read_text(encoding='utf-8'),'@@SCENES@@':base64.b64encode((root/'assets/landscape.wasm').read_bytes()).decode(),'@@CATALOG@@':json.dumps(catalog),'@@FISH@@':image(root/'assets/fish.png'),'@@WASM@@':base64.b64encode((root/'assets/atlas.wasm').read_bytes()).decode(),'@@DEVICE_UI@@':(root/'src/device-ui.js').read_text(encoding='utf-8').strip()}
for token,value in values.items():
 assert template.count(token)==1,token
 template=template.replace(token,value)
(root/'Thai-Waters-play.html').write_text(template,encoding='utf-8')
