"""Show side elevations of the selected native slices, including removable supports."""
from pathlib import Path
import re,sys
from PIL import Image,ImageDraw,ImageFont
from kit import HERE
def elevation(p,axis,ids):
    cat='';oid='';z=0;last=[0,0];wid=.42;lines=[];debt=0
    for ln in p.open():
        if ln.startswith('; Z_HEIGHT:'):z=float(ln.split(':')[-1]);oid=''
        elif ln.startswith('; FEATURE:'):cat=ln.split(':')[-1].strip()
        elif ln.startswith('; LINE_WIDTH:'):wid=float(ln.split(':')[-1])
        elif ln.startswith(('; start printing object, unique label id:', '; OBJECT_ID:')):oid=ln.split(':')[-1].strip()
        elif ln.startswith('; stop printing object'):oid=''
        elif ln.startswith(('G0 ','G1 ','G2 ','G3 ')):
            a={k:float(v) for k,v in re.findall(r' ([XYE])(-?[\d.]+)',ln.split(';')[0])}
            old=last;last=[a.get('X',old[0]),a.get('Y',old[1])];e=a.get('E',0)
            if e<0:debt-=e;continue
            recovered=min(debt,e);debt-=recovered
            if oid in ids and e>recovered and last!=old and cat not in ('Custom','Skirt','Prime tower','Flush'):
                lines.append((cat,old[axis],last[axis],z,wid))
    return lines
def draw(plate1,plate3,out):
    im=Image.new('RGB',(1130,650),'#f7f5ee');d=ImageDraw.Draw(im)
    def font(n,b=False):return ImageFont.truetype('arialbd.ttf' if b else 'arial.ttf',n)
    d.text((28,22),'45° print orientations',font=font(34,True),fill='#1c3934')
    d.text((29,69),'Bambu Studio toolpaths viewed from the side  ·  X1 Carbon  /  0.4 mm  /  PolyTerra PLA',font=font(20),fill='#405750')
    for i,(p,a,oid,label) in enumerate([(plate1,0,'385','01   Housing'),(plate3,1,'396','03   Rod handle')]):
        paths=elevation(p,a,{oid});lo=min(min(u,v) for _,u,v,_,_ in paths);hi=max(max(u,v) for _,u,v,_,_ in paths)
        zmax=max(l[3] for l in paths);base=532;ox=30+i*552;scale=min(484/(hi-lo),365/zmax)
        d.rounded_rectangle((ox,114,ox+518,570),10,fill='#e8ede8')
        d.text((ox+15,129),label,font=font(24,True),fill='#203931')
        for kind in ['support','brim','model']:
            for cat,u,v,z,w in paths:
                c='support' if cat.startswith('Support') else ('brim' if cat=='Brim' else 'model')
                if c==kind:
                    x=ox+259;mid=(lo+hi)/2;d.line((x+(u-mid)*scale,base-z*scale,x+(v-mid)*scale,base-z*scale),fill={'support':'#ca8153','brim':'#242f39','model':'#527565'}[c],width=max(1,round(w*scale)))
        d.line((ox+10,base+2,ox+508,base+2),fill='#334740',width=2)
    d.text((32,594),'Green   Printed part',font=font(21,True),fill='#426956')
    d.text((344,594),'Ochre   Removable support',font=font(21,True),fill='#965221')
    d.text((801,594),'Dark line   Build surface',font=font(21),fill='#334740')
    im.save(out)
if __name__=='__main__':draw(Path(sys.argv[1]),Path(sys.argv[2]),HERE/'plate-key.png')
