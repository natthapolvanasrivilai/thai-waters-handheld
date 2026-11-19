"""Pack the inspection page and its font, assets and renderer as one offline file."""
import argparse,base64,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;repo=HERE.parents[3]
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
s=(HERE/'template.html').read_text(encoding='utf-8-sig')
license=(repo/'game/assets/fonts/OFL.txt').read_text(encoding='utf-8')
three_license=(repo/'third-party/three-LICENSE.txt').read_text(encoding='utf-8')
font=base64.b64encode((repo/'game/assets/fonts/AtkinsonHyperlegibleNext.ttf').read_bytes()).decode()
for key,val in [('FONT',font),('MESH',(args.work/'meshes.json').read_text(encoding='utf8')),
                ('CHECKS',(HERE/'placement-results.json').read_text(encoding='utf8')),('VIEW',(args.work/'renderer.js').read_text(encoding='utf8'))]:
    s=s.replace('@@'+key+'@@',val)
s=s.replace('</html>','<!--\n'+license+'\n'+three_license+'\n-->\n</html>')
args.output.write_text(s,encoding='utf-8')
