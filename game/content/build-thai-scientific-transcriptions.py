"""Deterministic approximate Thai-script reading aid, never a vernacular-name source."""
import argparse,json,re,unicodedata
from pathlib import Path

_BINOMIAL=re.compile(r'^[A-Z][a-z]+ [a-z]{2,}$')
_VOWELS={'ae','oe','aa','ee','ii','oo','uu','ai','au','eu','ou','a','e','i','o','u','y'}
_VRUN=re.compile('|'.join(sorted(_VOWELS,key=lambda v:(-len(v),v))))
_ONSET={'b':'บ','c':'ค','d':'ด','f':'ฟ','g':'ก','h':'ฮ','j':'ย','k':'ค','l':'ล','m':'ม','n':'น','p':'ป','q':'ค','r':'ร','s':'ส','t':'ต','v':'ว','w':'ว','x':'ซ','z':'ซ',
        'ph':'ฟ','th':'ท','ch':'ค','sh':'ช','rh':'ร','kh':'ข','wh':'ว','qu':'คว','ng':'ง','gn':'กน','sc':'สก',
        'bl':'บล','br':'บร','cl':'คล','cr':'คร','dr':'ดร','fl':'ฟล','fr':'ฟร','gl':'กล','gr':'กร','kl':'คล','kr':'คร','pl':'ปล','pr':'ปร','tr':'ตร','vr':'วร'}
_CODA={'b':'บ','c':'ก','d':'ด','f':'ฟ','g':'ก','h':'ห์','j':'ย','k':'ก','l':'ล','m':'ม','n':'น','p':'ป','q':'ก','r':'ร','s':'ส','t':'ต','v':'ฟ','w':'ว','x':'กซ์','z':'ซ',
       'ng':'ง','ph':'ฟ','th':'ท','ch':'ช','sh':'ช','ck':'ก','nk':'งก','ks':'กซ์','ps':'ปส์','ts':'ตส์'}
_CODA_FORMS={
'a':('า','ั'), 'e':('เ','เ-'), 'i':('ิ','ิ'), 'o':('โ','อ'), 'u':('ุ','ุ'), 'y':('ิ','ิ'),
'aa':('า','า'), 'ae':('ี','ี'), 'oe':('ี','ี'), 'ee':('ี','ี'),'ii':('ี','ี'),'oo':('ู','ู'),'uu':('ู','ู'),
'ai':('ไ','ไ'), 'au':('เ-า','เ-า'), 'eu':('ิว','ิว'), 'ou':('ู','ู')
}
def _onset(text,v):
    if not text:return 'อ'
    if text=='c' and v[0] in 'eiy':return 'ซ'
    if text=='s' and v[0] in 'iy':return 'ซ'
    if text in _ONSET:return _ONSET[text]
    if len(text)>=2 and len(set(text))==1:return _onset(text[-1],v)
    return ''.join(_ONSET[t] for t in text)
def _coda(text):
    if text in _CODA:return _CODA[text]
    if not text:return ''
    if len(set(text))==1:return _CODA[text[0]]
    return ''.join(_CODA[c] for c in text)
def _syll(on,v,co):
    onset=_onset(on,v); template=_CODA_FORMS[v][bool(co)]
    stem=template.replace('-',onset) if '-' in template else (template+onset if template in ('เ','โ','ไ','แ') else onset+template)
    if on=='sc' and template in ('เ','โ','ไ','แ'):stem='ส'+template+'ก'
    return stem+_coda(co)
def _span(con):
    if not con:return '',''
    if con in _ONSET or con in ('cc','tt','pp','ss','rr','ll','mm','nn'):return '',con
    for n in (2,1):
        if len(con)>=n and con[-n:] in _ONSET:
            return con[:-n],con[-n:]
    return con[:-1],con[-1:]
def _word(name):
    name=name.lower()
    # Familiar loan/readings take precedence over the generic grapheme mapping.
    known={'channa':'แชนนา','carcharhinus':'คาร์คารินุส','hippocampus':'ฮิปโปแคมปัส','danio':'ดานิโอ','pseudogobius':'ซูโดโกบิอุส'}
    if name in known:return known[name]
    vs=list(_VRUN.finditer(name))
    if not vs:return _onset(name,'a')
    out=[]; onset=name[:vs[0].start()]
    for i,m in enumerate(vs):
        if i+1<len(vs):
            co,nxt=_span(name[m.end():vs[i+1].start()])
        else:
            co,nxt=name[m.end():],''
        out.append(_syll(onset,m.group(),co)); onset=nxt
    return ''.join(out)
def transliterate_scientific(text):
    if not _BINOMIAL.fullmatch(text):raise ValueError(f'Not a controlled ASCII binomial: {text!r}')
    return unicodedata.normalize('NFC',' '.join(_word(x) for x in text.split()))
def data(rows):
    names={}
    for row in rows:
        if not row.get('key'):continue
        name=row['name']
        if name in names:raise ValueError(f'duplicate: {name}')
        names[name]=transliterate_scientific(name)
    return {'format':'pocket-reel-thai-scientific-transcriptions/v1','names':dict(sorted(names.items()))}

if __name__=='__main__':
    folder=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,default=folder/'catalog.json')
    parser.add_argument('--extended',type=Path,default=folder/'extended.json')
    parser.add_argument('--output',type=Path,default=folder/'thai-scientific-transcriptions.json')
    args=parser.parse_args()
    first=json.loads(args.catalog.read_text(encoding='utf-8'))['fish']
    extra=json.loads(args.extended.read_text(encoding='utf-8'))
    out=data([*first,*extra])
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Thai-script binomials:',len(out['names']),'distinct readings:',len(set(out['names'].values())))
