const languageKey='thai-waters-language';
let language='th';
try{if(localStorage.getItem(languageKey)==='en')language='en';}catch{}
const thaiMessages={...@@DICTIONARY@@,
 'Natural debris':'วัสดุธรรมชาติ','Litter':'ขยะที่เก็บได้','Lost tackle':'อุปกรณ์ตกปลาที่หลุดหาย','Lost gear':'อุปกรณ์ที่หลุดหาย','Species data credits':'แหล่งข้อมูลชนิดปลา','Effects volume':'ระดับเสียงเอฟเฟกต์','Rum rice bran':'รำหมักเหล้ารัม','Tap to continue':'แตะเพื่อไปต่อ','Save catch & keep fishing':'บันทึกปลาแล้วตกต่อ','Language':'ภาษา','EST. WEIGHT':'น้ำหนักโดยประมาณ','TOTAL LENGTH':'ความยาวรวม','BODY LENGTH':'ความยาวลำตัว','RECORDED SIZE':'ขนาดที่บันทึก','MANTLE LENGTH':'ความยาวลำตัวหมึก','DISK WIDTH':'ความกว้างลำตัว','DISC WIDTH':'ความกว้างลำตัว','CARAPACE LENGTH':'ความยาวกระดอง','Origin':'แหล่งที่พบ','Fictional':'สายพันธุ์สมมติ','family illustration':'ภาพตัวแทนของวงศ์','cm':'ซม.','kg':'กก.','g':'ก.','species':'ชนิด','best':'สถิติสูงสุด','caught':'ครั้งที่จับได้','Page':'หน้า','turns':'รอบ','samples':'ตัวอย่าง','rank':'อันดับ','minimum':'ขั้นต่ำ','Casting':'กำลังเหวี่ยงเบ็ด','Recovered':'เก็บได้','length':'ความยาว','Language / ภาษา':'ภาษา'};
const escapePattern=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const phrases=Object.keys(thaiMessages).filter(k=>k.trim()&&/[a-z]/i.test(k)).sort((a,b)=>b.length-a.length);
// Compile once. Keep technical identifiers and scientific species names intact.
const phrasePattern=new RegExp('(^|[^A-Za-z])('+phrases.map(escapePattern).join('|')+')(?=$|[^A-Za-z])','g');
const messageCache=new Map();
function L(value){
 if(language!=='th'||typeof value!=='string'||!/[a-z]/i.test(value))return value;
 if(Object.hasOwn(thaiMessages,value))return thaiMessages[value];
 const trim=value.trim();
 if(Object.hasOwn(thaiMessages,trim))return value.replace(trim,()=>thaiMessages[trim]);
 if(messageCache.has(value))return messageCache.get(value);
 const result=value.replace(phrasePattern,(_,before,key)=>before+thaiMessages[key]);
 if(messageCache.size>1536)messageCache.clear();
 messageCache.set(value,result);return result;
}
const staticText=[],staticAttrs=[],updates=new WeakMap();
const staticRoot=document.querySelector('main');
const staticWalker=document.createTreeWalker(staticRoot,NodeFilter.SHOW_TEXT);
while(staticWalker.nextNode()){
 const node=staticWalker.currentNode;
 if(node.data.trim())staticText.push([node,node.data]);
}
for(const el of staticRoot.querySelectorAll('*')){
 if(el.tagName==='OPTION'&&!el.hasAttribute('value'))el.value=el.text;
 for(const attr of ['aria-label','title','placeholder','data-description']){
  if(el.hasAttribute(attr))staticAttrs.push([el,attr,el.getAttribute(attr)]);
 }
}
function setUi(el,raw){
 const value=String(raw??'');updates.set(el,value);
 const rendered=L(value);if(el.textContent!==rendered)el.textContent=rendered;
}
const thaiWords=typeof Intl.Segmenter==='function'?new Intl.Segmenter('th',{granularity:'word'}):null;
const thaiChars=typeof Intl.Segmenter==='function'?new Intl.Segmenter('th',{granularity:'grapheme'}):null;
function wrapTokens(text){
 if(!/[\u0e00-\u0e7f]/.test(text))return text.match(/\S+\s*|\s+/g)||[];
 return thaiWords?Array.from(thaiWords.segment(text),v=>v.segment):Array.from(text.normalize('NFC').matchAll(/.[\u0e31\u0e34-\u0e3a\u0e47-\u0e4e]*/gu),m=>m[0]);
}
function* layoutSegments(text){
 if(!/[\u0e00-\u0e7f]/.test(text)){yield* text.matchAll(/\S+/g);return;}
 if(thaiChars){for(const s of thaiChars.segment(text))if(s.segment.trim())yield {0:s.segment,index:s.index};}
 else yield* text.matchAll(/\S[\u0e31\u0e34-\u0e3a\u0e47-\u0e4e]*/gu);
}
