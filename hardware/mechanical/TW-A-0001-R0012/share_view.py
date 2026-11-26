"""Publish measured harness motion; keep supplier meshes in the local full-model viewer."""
import argparse
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
DATA = re.compile(r'(<script type="application/json" id="data">)(.*?)(</script>)',re.S)
LOADER = """
<section id="local-model"><h3>Inspect the actual connector</h3>
<p>This view shows the four flexing leads, stationary loom and measured gaps. Load the local R0012 connector viewer to inspect the molded latch and contacts.</p>
<label>Select local viewer <input type="file" id="file" accept=".html,text/html"></label>
<p id="file-status" role="status"></p></section>
<script>
document.getElementById('file').addEventListener('change', async event => {
 const file=event.target.files[0]; if(!file)return;
 const status=document.getElementById('file-status');
 try {
  const source=await file.text();
  const parsed=new DOMParser().parseFromString(source,'text/html');
  const data=JSON.parse(parsed.getElementById('data').textContent);
  if(!data.items.rocker||!data.items.housing||data.qa.revision!=='TW-A-0001-R0012')
    throw new Error('Choose the R0012 connector-motion HTML built with the supplier files.');
  // Run only the bundled project renderer. Import model data, never code from the selected file.
  const local=document.createElement('iframe');local.title='Full CviLux connector motion';
  local.setAttribute('sandbox','allow-scripts');local.style='width:100%;height:94vh;border:0';
  const template=document.documentElement.cloneNode(true);
  template.removeAttribute('data-ready');
  template.removeAttribute('data-motion');
  template.querySelector('#local-model').remove();
  template.querySelector('body').removeAttribute('data-wire-study');
  const cameraButton=template.querySelector('#closeup');if(cameraButton)cameraButton.textContent='Latch close-up';
  template.querySelectorAll('#stage canvas').forEach(c=>c.remove());
  template.querySelector('#data').textContent=JSON.stringify(data).replace(/</g,String.fromCharCode(92)+'u003c');
  template.querySelector('header h1').textContent='CviLux plug withdrawal';
  template.querySelector('#loading').hidden=false;
  template.querySelector('aside section').hidden=false;
  local.srcdoc='<!doctype html>'+template.outerHTML;
  document.body.replaceChildren(local);
 }catch(err){status.textContent=err.message;}
});
</script>
"""
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("full",type=Path)
    args=parser.parse_args()
    html=args.full.read_text(encoding="utf-8")
    here=DATA.search(html)
    data=json.loads(here[2])
    revision=data["qa"]["revision"]
    assert revision in ("TW-A-0001-R0012","TW-A-0001-R0013")
    label=revision.rsplit("-",1)[-1]
    # Permit only project-authored loom geometry. Keep all solver measurements and wire trajectories.
    data["items"]={name:obj for name,obj in data["items"].items()
                   if name.startswith(("w1","tee-","wh")) and "motion" in obj}
    assert len(data["items"])>=8
    data["section"]={k:[] for k in data["section"]}
    html=html[:here.start(2)]+json.dumps(data,separators=(",",":"))+html[here.end(2):]
    html=re.sub(rf'<a href="{revision}-exploded.html">.*?</a>',"",html,count=1)
    html=html.replace("<h1>CviLux plug withdrawal</h1>","<h1>Harness withdrawal clearance</h1>")
    html=html.replace("<aside class=\"card\"><section>","<aside class=\"card\"><section hidden>",1)
    html=html.replace('<body>','<body data-wire-study>',1)
    html=html.replace('</style>', '[data-wire-study] .legend span:nth-child(-n+2){display:none} '
                      '[data-wire-study] .buttons label:has(#context){display:none}</style>',1)
    html=html.replace('id="closeup">Latch close-up','id="closeup">Crimp ends',1)
    html=html.replace('</aside>',LOADER.replace('R0012',label)+'</aside>',1)
    html=html.replace("document.getElementById('file').addEventListener","document.getElementById('file')?.addEventListener")
    out=HERE.parents[2]/"docs/models"/(revision+"-motion-review.html")
    out.write_text(html,encoding="utf-8")
    print(out)
if __name__=="__main__":
    main()
