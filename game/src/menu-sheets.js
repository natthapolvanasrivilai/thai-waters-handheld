// Keep each activity on a fixed-size sheet. Existing controls keep their state
// and event listeners as players move between sheets.
const menuSheets=(()=>{
 const bar=menu.querySelector(':scope > .menubar'),title=$('menuTitle'),pages=new Map(),positions=new Map();
 const homeLanguage=$('languageRow');bar.insertBefore(homeLanguage,$('resume'));
 const prev=arrow('back','Previous'),next=arrow('next','Next'),counter=document.createElement('small');
 counter.id='sheetNumber';prev.id='sheetPrev';next.id='sheetNext';bar.insertBefore(prev,$('resume'));bar.insertBefore(counter,$('resume'));bar.insertBefore(next,$('resume'));
 function arrow(icon,label){const b=document.createElement('button');b.type='button';b.dataset.navicon=icon;b.title=L(label);b.setAttribute('aria-label',b.title);return b;}
 function panel(name){return menu.querySelector('[data-section="'+name+'"]');}
 function add(name,en,th,...nodes){
  const el=document.createElement('div');el.className='menu-sheet';el.hidden=true;
  const list=pages.get(name)||[];list.push({el,en,th});pages.set(name,list);
  el.append(...nodes);panel(name).append(el);
 }
 const field=id=>$(id).closest('.lcd-choice'),box=id=>$(id).closest('.bindings');
 function row(...nodes){const d=document.createElement('div');d.className='sheet-row';d.append(...nodes);return d;}
 const spots=panel('spots'),tip=spots.querySelector(':scope > small');
 add('spots','Destination','หมายตกปลา',row(box('searchSpot'),$('locationMapOpen')),row(field('places'),$('fishHere')));
 add('spots','Conditions','สภาพหมาย',box('period'),$('travelStory'),tip);
 add('spots','Fishing map','แผนที่ตกปลา',$('mapGraphic'),$('mapAccess'));
 pages.get('spots')[2].el.id='waterbodyMapSheet';
 const rod=panel('rod');
 add('rod','Tackle','ชุดตกปลา',row(field('technique'),field('finish')),box('hookBait'));
 add('rod','Bait notes','วิธีใช้เหยื่อ',rod.querySelector('.bait-preview'),$('techniqueNote'));
 add('rod','Journey','เส้นทางนักตกปลา',rod.querySelector('.book-totals'),$('chapter'),$('letter'),$('goal'));
 add('rod','Upgrades','อัปเกรด',$('builds'));
 add('rod','Tackle points','แต้มอุปกรณ์',$('refund'),rod.querySelector('.note'));
 add('rod','Career & backups','บันทึกนักตกปลา',$('careerOpen'));
 add('career','Local career','บันทึกในเครื่อง',$('careerSummary'),$('careerPrivacy'),$('careerExport'));
 add('career','Restore backup','กู้คืนไฟล์สำรอง',$('careerFile').closest('label'),$('careerStatus'),$('careerRestore'));

 const sound=panel('sound'),rumble=sound.querySelector('.rumble-box');
 add('sound','Music','ดนตรี',row(field('music'),field('volume')),sound.querySelector('.audio-check'));
 add('sound','Fishing sounds','เสียงตกปลา',row(field('cue'),field('fx')),row(field('reelClick'),$('iosSwitchRow')));
 add('sound','Rod rumble','แรงสั่น',row(field('rumbleLevel'),$('testPhoneMotor')),$('rumbleStatus'));
 const pulses=[...rumble.querySelectorAll('[data-pulse]')];
 add('sound','Feel the bite','ทดสอบแรงสั่น',row(...pulses.slice(0,2)),row(...pulses.slice(2)),$('rumbleLamp'));
 const pulseStatus=document.createElement('small');pulseStatus.setAttribute('role','status');
 pulses[0].closest('.menu-sheet').append(pulseStatus);
 new MutationObserver(()=>{pulseStatus.textContent=$('rumbleStatus').textContent;}).observe($('rumbleStatus'),{childList:true,subtree:true,characterData:true});
 rumble.remove();sound.querySelector('.opts').remove();
 const sensors=panel('sensors'),notes=[...sensors.querySelectorAll(':scope > p:not([id])')];
 add('sensors','Calibrate rod','ตั้งค่าคันเบ็ด',box('enableMotion'),$('motionStatus'),$('sensorRead'));
 add('sensors','Wrist reel','หมุนข้อมือ',$('wristReel').closest('label'),$('wristRead'),notes[0]);
 add('sensors','Bench inputs','ทดสอบอินพุต',row(field('simBattery'),$('tilt').closest('label')),notes[1]);
 add('sensors','Paired rod','คันเบ็ดที่จับคู่',$('handheldEnable').closest('fieldset'));
 const crew=panel('crew'),standingsNote=$('cupScope').nextElementSibling,crewHeading=$('crewHelp').previousElementSibling;
 add('crew','Daily cup','แข่งประจำวัน',$('cupTarget'),$('cupLocation'),$('cupLoadout'),box('cupTravel'),$('cupTravelNote'),$('cupMine'));
 crew.querySelector(':scope > h2').remove();
 add('crew','Standings','อันดับ',$('cupScope'),standingsNote,$('cupLeaders'),$('cupEmpty'));
 add('crew','Crew challenge','ทีมตกปลา',$('crewHelp'),$('joinCrew'),$('crewStatus'));crewHeading.remove();
 function open(name){
  const list=pages.get(name)||[],at=positions.get(name)||0;
  homeLanguage.hidden=name!=='home'&&name!=='boot-home';prev.hidden=next.hidden=counter.hidden=!list.length;
  if(!list.length)return;
  list.forEach((page,i)=>page.el.hidden=i!==at);
  title.textContent=language==='th'?list[at].th:list[at].en;
  if(name==='spots'&&at===2)list[at].el.dispatchEvent(new Event('spots-map-visible'));
  counter.textContent=(at+1)+'/'+list.length;prev.disabled=at===0;next.disabled=at===list.length-1;
  prev.title=L('Previous');next.title=L('Next');prev.setAttribute('aria-label',prev.title);next.setAttribute('aria-label',next.title);
 }
 function step(by){const pagesHere=pages.get(menuPage);if(!pagesHere)return;positions.set(menuPage,Math.max(0,Math.min(pagesHere.length-1,(positions.get(menuPage)||0)+by)));open(menuPage);}
 prev.onclick=()=>step(-1);next.onclick=()=>step(1);
 return {open,go(name,at){if(menuPage!==name||!pages.get(name)?.[at])return false;positions.set(name,at);open(name);return true;},reset:name=>positions.delete(name)};
})();
