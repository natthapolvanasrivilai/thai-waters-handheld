"""Arrange native Bambu Studio preview images into a printable plate key."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageDraw,ImageFont
import sys
HERE=Path(__file__).resolve().parent
names=['Housing and lamp shelf','Bezel and reel','Rod handle','Single status diffuser','Mask and service cover','Battery gauges','PCB and component gauges','Reel controls and power cap']
labels=['SAGE PETG','CHARCOAL PETG','SAGE PETG','CLEAR PETG','BLACK TPU','GRAY PETG','GRAY PETG','AMBER PETG']
cols=['#899C89','#303938','#899C89','#E6F2F2','#202221','#92979A','#92979A','#D99A4E']
def make(path):
    out=Image.new('RGB',(1280,606),'#f5f4ed');draw=ImageDraw.Draw(out)
    def font(sz):return ImageFont.truetype('arial.ttf',sz)
    draw.text((22,10),'Thai Waters  /  X1 Carbon print plates',font=font(31),fill='#263634')
    with ZipFile(path) as z:
        for i,(n,label,col) in enumerate(zip(names,labels,cols),1):
            im=Image.open(BytesIO(z.read(f'Metadata/plate_{i}.png'))).convert('RGBA')
            im=im.crop(im.getbbox());im.thumbnail((278,160),Image.Resampling.LANCZOS)
            x=16+((i-1)%4)*315;y=62+((i-1)//4)*268
            draw.rounded_rectangle((x,y,x+304,y+253),10,fill='#e6e8e0')
            out.paste(im,(int(x+(304-im.width)/2),int(y+9+(164-im.height)/2)),im)
            draw.text((x+12,y+182),f'{i:02}   {n}',fill='#263634',font=font(19))
            draw.rounded_rectangle((x+12,y+218,x+31,y+236),4,fill=col,outline='#626c65')
            draw.text((x+39,y+217),label,fill='#3e4e46',font=font(16))
    out.save(HERE/'plate-key.png')
if __name__=='__main__':make(sys.argv[1])
