from pathlib import Path
from xml.sax.saxutils import escape
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
p=Path("Pocket-Reel-Hardware-Specification-HWS-001.md")
for n,f in [("Text","DejaVuSans.ttf"),("Bold","DejaVuSans-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(n,"/usr/share/fonts/truetype/dejavu/"+f))
pdfmetrics.registerFontFamily("Text",normal="Text",bold="Bold")
def style(name, size, lead, sb=0, sa=0, bold=False):
    return ParagraphStyle(name,fontName="Bold" if bold else "Text",fontSize=size,leading=lead,spaceBefore=sb,spaceAfter=sa,textColor=colors.HexColor("#171717"))
st={k:v for k,v in [
 ("h1",style("Title",21,26,3,8,True)),("h2",style("Section",13,17,13,6,True)),
 ("h3",style("Small head",10.5,14,12,4,True)),("body",style("Body",9.0,12.4,0,6)),
 ("cell",style("Cell",8.35,10.55)),("head",style("Head",8.35,10.55,0,0,True)),
 ("note",style("Metadata",8.3,12,0,13,True))]}
def fmt(s):
    s=escape(s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)',r'<link href="\2"><u>\1</u></link>',s)
    return s
story=[]
lines=p.read_text().splitlines()
i=0
while i<len(lines):
    l=lines[i];i+=1
    if not l.strip():continue
    if l.startswith("|"):
        group=[l]
        while i<len(lines) and lines[i].startswith("|"):
            group.append(lines[i]);i+=1
        cells=[row.strip().strip("|").split("|") for row in group if not re.fullmatch(r"[|:\- ]+",row)]
        widths=[102,157,250] if len(cells[0])==3 else [120,389]
        data=[[Paragraph(fmt(c.strip()),st["head" if j==0 else ("head" if k==0 else "cell")]) for k,c in enumerate(row)] for j,row in enumerate(cells)]
        table=Table(data,colWidths=widths,repeatRows=1,hAlign="LEFT")
        table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),3.5),("BOTTOMPADDING",(0,0),(-1,-1),3.5),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f6f6f6")]),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e8e8e8")),("LINEBELOW",(0,0),(-1,0),0.6,colors.HexColor("#777777")),("LINEBELOW",(0,-1),(-1,-1),0.6,colors.HexColor("#777777"))]))
        story.append(table)
    else:
        if l.startswith(("## 2.","## 3.")):story.append(PageBreak())
        if l.startswith("### "):kind,l="h3",l[4:]
        elif l.startswith("## "):kind,l="h2",l[3:]
        elif l.startswith("# "):kind,l="h1",l[2:]
        elif l.startswith("**HWS-"):kind="note"
        else:kind="body"
        story.append(Paragraph(fmt(l),st[kind]))
def frame(c,d):
    w,h=A4;c.setStrokeColor(colors.HexColor("#777777"));c.line(43,37,w-43,37);c.setFont("Text",7.5)
    c.drawString(43,25,"POCKET REEL  /  HWS-001  /  REV 0.3");c.drawRightString(w-43,25,f"ENGINEERING HOLD  /  {d.page}")
doc=SimpleDocTemplate(str(p.with_suffix(".pdf")),pagesize=A4,title="Pocket Reel Hardware Specification HWS-001",author="MALIEV Engineering",topMargin=37,bottomMargin=48,leftMargin=43,rightMargin=43)
doc.build(story,onFirstPage=frame,onLaterPages=frame)
