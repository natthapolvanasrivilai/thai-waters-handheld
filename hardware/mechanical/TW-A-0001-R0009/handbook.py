"""Refresh the current private handbook with registered review geometry and one-unit costs."""
import argparse
import base64,csv,gzip,hashlib,html,json,re
from pathlib import Path
from urllib.parse import quote
here=Path(__file__).resolve().parent
root=here.parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--game',type=Path,default=root/'game/Thai-Waters-play.html',help='Standalone build matched to the intended software release')
game=parser.parse_args().game
doc=root/'docs/index.html' 
url='https://github.com/natthapolvanasrivilai/thai-waters-handheld/blob/main/'
page=doc.read_text(encoding='utf8')
def update_script(name,body):
    global page
    pattern=r'(<script id="'+name+r'"[^>]*>)[^<]*(</script>)'
    page,n=re.subn(pattern,lambda m:m[1]+body+m[2],page,count=1)
    assert n==1,name
def insert_marked(page,start,end,content):
    a=page.index(start);b=page.index(end,a)
    return page[:a]+content+page[b:]
sourcing=root/'sourcing/production-intent'
budget=json.loads((sourcing/'R0009-budget.json').read_text())
parts=list(csv.DictReader((sourcing/'R0009-prototype-budget.csv').open(encoding='utf-8-sig')))
data=json.loads(re.search(r'<script id="reviewData"[^>]*>(.*?)</script>',page,re.S)[1])
def link(source):
    if source.startswith('https://'):return source
    path,_,anchor=source.partition('#')
    if not (root/path).is_file():raise ValueError('Missing BOM source '+source)
    return url+quote(path,safe='/')+('#'+anchor if anchor else '')
data['bom']=[{'Ref':r['Ref'],'Variant':r['group'],'Description':r['Description'],'MPN or process':r['mpn'],'Qty per unit':r['qty'],'UOM':r['UOM'],'USD at 1':r['price'],'Ext USD':r['ext'],'Price basis':r['basis'],'Source':r['mpn'],'Source URL or drawing':link(r['url'])} for r in parts]
data['productionIntro']='R0009 / R0003 is the current engineering review. R0008 / R0002 remains the released inert-fit baseline. Record connector polarity, service clearances and optical isolation on a first article.'
data['prototypeBudget']=budget
update_script('reviewData',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<',r'\u003c'))
for key,path in [('compressedGame',game),('compressedModel',root/'docs/models/TW-A-0001-R0009-exploded.html')]:
    update_script(key,base64.b64encode(gzip.compress(path.read_bytes(),mtime=0)).decode())
page=page.replace('R0008 fit print · R0002 electrical','R0009 design review · R0003 electrical')
page=page.replace('R0008 exploded mechanical assembly viewer','R0009 dressed mechanical assembly viewer')
page=page.replace('R0008 print setup and assembly','R0008 released inert print reference')
page=page.replace('Variant<select id="partVariant"','Cost group<select id="partVariant"')
page=page.replace('Unit economics and launch','Rev F historical batch scenarios').replace('<h3>Buy / make BOM</h3>','<h3>R0009 full prototype BOM</h3>')
page=insert_marked(page,'const bomGrid=',';\n',"""const bomGrid=rs=>tbl(['Ref · group','Component / process','Qty','USD each','USD per build','Part or drawing'],rs.map(r=>[html(r.Ref+' · '+r.Variant),html(r.Description),html(r['Qty per unit']+' '+r.UOM),num(+r['USD at 1'],4),num(+r['Ext USD'],3),source(r['Source URL or drawing'],r.Source)+'<br><small>'+html(r['Price basis'])+'</small>']))""")
extra="""<script id="current-hardware-review">
(function(){
 const a=document.getElementById('assembly'), v=document.getElementById('viewer');
 const lead=v.previousElementSibling;
 const heading=document.createElement('div');
 heading.innerHTML='<h2>R0009 engineering assembly</h2><p>Inspect the fitted speaker, three status lights, folding reel and dressed cables. Select Harness and a conductor to inspect the route. Check connector polarity, strain relief and the accessible disconnect on a physical build.</p>';
 a.prepend(heading,lead,v);
 const biz=document.getElementById('business'), budget=D.prototypeBudget;
 const top=document.createElement('div');
 top.innerHTML='<h2>One full R0009 prototype</h2>'+cards([[usd(budget.materials_usd),'Allocated parts and retail pack'],[usd(budget.conversion_usd),'Labor, printer and energy'],[usd(budget.assembled_usd),'Assembled before freight and tax']])+cellTable(['BOM group','USD per build'],Object.entries(budget.groups_usd).map(([k,v])=>[k,usd(v)]))+'<p>One unit with reel, rumble and rod. Supplier packs and PCB setup affect checkout. Selling-price test for the full set: ฿5,490 Thailand direct or US$169 before sales tax. The batch model below retains its historical Rev F assumptions.</p>';
 biz.prepend(top);
 const section=biz.querySelector('#findPart').closest('.toolbar'),title=section.previousElementSibling,records=document.getElementById('parts')||section.nextElementSibling;
 top.after(title,section,records);
 const variants=document.getElementById('partVariant');variants.replaceChildren(...['All',...new Set(D.bom.map(r=>r.Variant))].map(v=>new Option(v,v)));
})();
</script>"""
page=re.sub(r'<script id="current-hardware-review">.*?</script>', '',page,flags=re.S)
before,end,tail=page.rpartition('</html>')
assert end
page=before+extra+end+tail
doc.write_text(page,encoding='utf8')
