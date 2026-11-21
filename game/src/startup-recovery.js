// Retry, backup preview, explicit temporary play and download only.
// This screen has no persistent commit or reload capability.
function bindStartupRecovery($,words,{retry,readRaw,parseBackup,download,useSession}){
 const panel=$('startupRecovery'),title=$('startupError'),backup=$('startupBackup');
 const retryButton=$('startupRetry'),input=$('startupRecoveryFile'),copy=$('startupRecoveryCopy'),status=$('startupRecoveryStatus');
 const use=$('startupRecoveryUseSession');
 let epoch=0,selected=null;
 const invalidate=()=>{selected=null;use.hidden=true;};
 const reset=()=>{epoch++;invalidate();input.value='';status.textContent='';};
 const visible=()=>!panel.hidden&&!backup.hidden;
 const say=(en,th)=>{status.textContent=words(en,th);};
 function hide(){reset();panel.hidden=true;}
 function show(career){
  reset();panel.hidden=false;backup.hidden=!career;
  title.textContent=career?words('Could not read your career','อ่านบันทึกการตกปลาไม่สำเร็จ'):words('Could not load Pocket Reel','โหลด Pocket Reel ไม่สำเร็จ');
  $('startupRecoveryNote').textContent=words('Your saved data was not changed.','ยังไม่ได้แก้ไขข้อมูลที่บันทึกไว้');
  retryButton.textContent=words('Try again','ลองอีกครั้ง');
  $('startupChooseLabel').textContent=words('Validate a local backup (does not restore)','ตรวจสอบไฟล์สำรองในเครื่อง (ไม่กู้คืนอัตโนมัติ)');
  use.textContent=words('Use backup for this session','ใช้ไฟล์สำรองเฉพาะรอบนี้');
  copy.textContent=words('Download unchanged save bytes','ดาวน์โหลดข้อมูลบันทึกเดิม');
  title.focus({preventScroll:true});
 }
 use.onclick=()=>{
  if(!visible()||!selected)return;
  const save=selected;reset();
  useSession(save);
 };
 retryButton.onclick=()=>{if(!panel.hidden)retry();};
 copy.onclick=()=>{
  if(!visible())return;
  try{
   const raw=readRaw();
   if(typeof raw!=='string'||raw.length>8*1024*1024)throw Error('No bounded copy');
   download(raw);
   say('Download requested. The saved data is unchanged.','ขอดาวน์โหลดแล้ว ข้อมูลที่บันทึกไว้ไม่เปลี่ยนแปลง');
  }catch{say('Could not read a copy of the current save.','ไม่สามารถอ่านสำเนาข้อมูลบันทึกปัจจุบันได้');}
 };
 input.onchange=async()=>{
  const request=++epoch,file=input.files?.[0];
  invalidate();status.textContent='';
  if(!file||!visible())return;
  try{
   if(file.size>8*1024*1024)throw Error('Too large');
   const text=await file.text();
   if(request!==epoch||!visible())return;
   const backup=parseBackup(text),count=backup.book.filter(([n])=>n>0).length;
   selected=backup;use.hidden=false;
   say('Valid backup: '+count+' species. Nothing written. Temporary play will not update your original save. Export before closing.','ไฟล์สำรองใช้ได้: '+count+' ชนิด ยังไม่ได้เขียนข้อมูล การเล่นรอบนี้จะไม่แก้บันทึกเดิม ดาวน์โหลดสำรองก่อนปิด');
  }catch{if(request===epoch&&visible())say('Could not validate this backup. Nothing changed.','ตรวจสอบไฟล์สำรองนี้ไม่สำเร็จ ไม่มีข้อมูลเปลี่ยนแปลง');}
 };
 return {hide,show};
}
// Web Storage exposes UTF-16 code units, not a byte encoding. Save a BOM plus
// each exact code unit, including lone surrogates in a damaged value.
function encodeRawCareerCopy(raw){
 const bytes=new Uint8Array(2+raw.length*2),data=new DataView(bytes.buffer);
 data.setUint16(0,0xfeff,true);
 for(let i=0;i<raw.length;i++)data.setUint16(2+i*2,raw.charCodeAt(i),true);
 return bytes;
}
if(typeof module!=='undefined'&&module.exports)module.exports={bindStartupRecovery,encodeRawCareerCopy};
