const cupKey='thai-waters-cup-v1';
let cupState={}, enteredCup=0, requestInFlight=false, cupNotice='';
try{cupState=JSON.parse(localStorage.getItem(cupKey))||{};enteredCup=cupState.joined||0;}catch{}
function rememberCup(){if(sessionOnly)return;try{localStorage.setItem(cupKey,JSON.stringify(cupState));}catch{}}
function currentCupDay(){return Math.floor((Date.now()+7*3600000)/86400000);}
function cupIsJoined(){return !sessionOnly&&enteredCup===currentCupDay();}
function tournamentGoal(){
 const day=currentCupDay(),spot=day*37%atlas.locations.length;
 const stock=atlas.fish.slice(0,52).filter(f=>f.site===atlas.locations[spot].pool);
 const f=stock[(Math.floor(day/atlas.locations.length)+day*7)%stock.length];
 return {day,spot,species:atlas.fish.indexOf(f),name:f.name,location:atlas.locations[spot].name,minimum:Math.ceil(f.low+(f.high-f.low)*.45)};
}
let cupBoard=null,rankPage=0;
const cupWords=(en,th)=>language==='th'?th:en;
function cupText(id,value){if($(id).textContent!==value)setUi($(id),value);}
function cupKit(species){
 if(!g)return null;
 const bait=g.recommendedBait(species);
 if(!Number.isInteger(bait)||bait<0||bait>=18)return null;
 // Recommend by feeding depth (not portrait body shape). Bottom jig,
 // midwater stop-and-go, surface drift; the engine supplies bait/depth.
 return {bait,rig:[0,1,2][Math.floor(bait/6)]};
}
function cupTravelReady(){return !!g&&powered&&!bootHome&&arrivalSince===null&&[0,6,9].includes(g.state());}
function drawCup(){
 const goal=cupBoard?.goal||tournamentGoal(), joined=!sessionOnly&&enteredCup===goal.day;
 const fish=atlas.fish[goal.species],kit=cupKit(goal.species),ready=!!kit&&cupTravelReady();
 const timing=goal.species===40?cupWords(' Fish at dusk or night.',' ตกช่วงพลบค่ำหรือกลางคืน'):goal.species===41?cupWords(' Fish at dawn or night.',' ตกช่วงรุ่งเช้าหรือกลางคืน'):'';
 const units=cupWords('cm','ซม.'),metric=g?L(readEngineText(g.measurement(goal.species,goal.minimum))):'';
 cupText('cupGoal',[fish.name,thaiNameNote(fish)].filter(Boolean).join(' · '));
 cupText('cupTargetSize',cupWords('Qualifying minimum: ','ขั้นต่ำที่เข้าเกณฑ์: ')+goal.minimum+' '+units+(metric?' · '+metric:''));
 const step=[1,2,5,10,20,25,50,100,250].find(n=>4*n>goal.minimum),limit=4*step;
 const mark=$('cupRulerMark'),position=(100*goal.minimum/limit)+'%';
 if(mark.style.left!==position)mark.style.left=position;
 const ticks=$('cupRulerTicks');
 // A canvas survives the projected LCD painter, which doesn't render CSS gradients.
 if(!ticks.dataset.drawn){
  const brush=ticks.getContext('2d');
  for(let i=0;i<=20;i++){
   const major=i%5===0,x=Math.min(ticks.width-1,Math.round(i*ticks.width/20));
   brush.fillStyle=major?'#694925':'#9a763f';
   brush.fillRect(x,major?1:6,1,major?10:5);
  }
  ticks.dataset.drawn='true';
 }
 const labels=$('cupRulerLabels');
 for(let i=0;i<5;i++){
  const label=labels.children[i],text=String(i*step)+(i===4?' '+units:'');
  if(label.textContent!==text){label.style.setProperty('--tick',i);label.textContent=text;}
 }
 const plot=$('cupPortrait');
 if(g&&plot.dataset.species!==String(goal.species)){
  const brush=plot.getContext('2d');brush.clearRect(0,0,plot.width,plot.height);brush.imageSmoothingEnabled=false;
  drawSpecimen(brush,goal.species,0,0,plot.width,plot.height);plot.dataset.species=String(goal.species);
 }
 cupText('cupLocation',atlas.locations[goal.spot].name+cupWords(' · closes at midnight, Bangkok time.',' · ปิดรับผลตอนเที่ยงคืน เวลาไทย')+timing);
 cupText('cupLoadout',kit?cupWords('Tackle: ','ชุดตกปลา: ')+$('technique').options[kit.rig].text+' · '+baitTip(goal.species):'');
 cupText('cupTravel',placeId===goal.spot?cupWords('Equip recommended tackle','ใส่ชุดที่แนะนำ'):cupWords('Equip and travel','ใส่ชุดแล้วเดินทาง'));
 cupText('cupJoin',joined?'Fishing this cup':'Enter daily cup');
 $('cupJoin').disabled=sessionOnly||bootHome||joined||requestInFlight||location.protocol==='file:';
 $('cupTravel').disabled=!ready;
 $('cupTravelNote').hidden=ready;
 cupText('cupTravelNote',ready?'':bootHome?cupWords('Resume fishing before changing tackle or traveling.','เล่นต่อก่อนเปลี่ยนชุดหรือลงหมาย'):cupWords('Finish this cast or file your catch first.','จบรอบตกปลาหรือบันทึกปลาที่ได้ก่อน'));
 cupText('cupScope',location.hostname.endsWith('.chatgpt.site')?'Private playtest standings':'Local host standings');
 cupText('cupMine',sessionOnly?cupWords('Daily Cup is unavailable in a temporary career.','งดแข่งขันถ้วยรายวันในโหมดเล่นชั่วคราว'):cupNotice||(cupBoard?.rank?cupBoard.angler+' · rank #'+cupBoard.rank+' · '+cupBoard.best+' cm':joined?(cupBoard?.angler||'Entered')+' · file a qualifying catch.':'Enter before landing your catch.'));
 const list=$('cupLeaders'),rows=cupBoard?.leaders||[];
 const per=4,pages=Math.max(1,Math.ceil(rows.length/per));rankPage=Math.min(rankPage,pages-1);
 const key=language+rankPage+JSON.stringify(rows);
 if(list.dataset.rows!==key){
  list.dataset.rows=key;list.replaceChildren();
  for(const r of rows.slice(rankPage*per,(rankPage+1)*per)){const line=document.createElement('div');setUi(line,'#'+r.rank+'  '+(r.you?'You':r.angler)+'  ·  '+r.cm+' cm');list.append(line);}
  if(pages>1){
   const nav=document.createElement('div');nav.className='history-nav';
   for(const dir of [-1,1]){
    const b=document.createElement('button');b.type='button';b.disabled=rankPage+dir<0||rankPage+dir>=pages;
    b.setAttribute('aria-label',L(dir<0?'Previous':'Next'));b.append(journalIcon(dir<0?'back':'next'));
    b.onclick=()=>{rankPage+=dir;drawCup();};nav.append(b);
   }
   nav.insertBefore(document.createTextNode((rankPage+1)+' / '+pages),nav.lastChild);list.append(nav);
  }
 }
 cupText('cupEmpty',!rows.length?(location.protocol==='file:'?'Open the hosted or LAN game to compete.':cupNotice?'Waiting for the event host.':cupBoard?'No qualifying catches yet.':'Connecting to the standings…'):'');
}
async function syncCup(action='view'){
 if(sessionOnly||bootHome){drawCup();return;}
 if(requestInFlight||location.protocol==='file:'){drawCup();return;}
 requestInFlight=true;
 try{
  const day=(cupBoard?.goal||tournamentGoal()).day;
  if(cupState.pending && cupState.pending.day<day){delete cupState.pending;rememberCup();}
  const report=cupState.pending&&action==='view'?cupState.pending:{action,day};
  const response=await fetch('/event/cup',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(report),signal:AbortSignal.timeout(5000)});
  if(!response.ok)throw Error();
  const board=await response.json();if(!board.goal||!Array.isArray(board.leaders))throw Error();
  cupBoard=board;enteredCup=board.joined?board.goal.day:0;cupState.joined=enteredCup;
  if(report.action==='file' && cupState.pending===report)delete cupState.pending;
  rememberCup();cupNotice='';
 }catch{cupNotice='Standings unavailable. Retry when connected.';}
 finally{requestInFlight=false;drawCup();}
}
function submitTournamentCatch(){
 if(sessionOnly)return;
 const goal=cupBoard?.goal||tournamentGoal();
 if(!pendingDay||pendingDay!==goal.day||placeId!==goal.spot||g.species()!==goal.species||g.lengthCm()<goal.minimum)return;
 const best=cupState.pending?.day===goal.day?cupState.pending.cm:0;
 cupState.pending={action:'file',day:goal.day,spot:placeId,species:g.species(),cm:Math.max(best,g.lengthCm())};
 rememberCup();void syncCup();
}
$('cupJoin').onclick=()=>syncCup('join');
$('cupTravel').onclick=()=>{
 if(!cupTravelReady())return;
 const goal=cupBoard?.goal||tournamentGoal(),kit=cupKit(goal.species);
 if(!kit||!atlas.locations[goal.spot])return;
 unlock();
 g.setTechnique(kit.rig);g.setBait(kit.bait);
 if(goal.spot===placeId){save();showRig();}
 else chooseSpot(goal.spot,goal.species===40?2:goal.species===41?3:timeMode);
 closeMenu();
};
setInterval(()=>{if(!sessionOnly&&powered&&!document.hidden&&(menu.open&&menuPage==='crew'||cupState.pending))syncCup();},10000);
