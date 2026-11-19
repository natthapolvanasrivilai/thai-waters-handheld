const cupKey='thai-waters-cup-v1';
let cupState={}, enteredCup=0, requestInFlight=false, cupNotice='';
try{cupState=JSON.parse(localStorage.getItem(cupKey))||{};enteredCup=cupState.joined||0;}catch{}
function rememberCup(){try{localStorage.setItem(cupKey,JSON.stringify(cupState));}catch{}}
function tournamentGoal(){
 const day=Math.floor((Date.now()+7*3600000)/86400000),spot=day*37%atlas.locations.length;
 const stock=atlas.fish.slice(0,52).filter(f=>f.site===atlas.locations[spot].pool);
 const f=stock[(Math.floor(day/atlas.locations.length)+day*7)%stock.length];
 return {day,spot,species:atlas.fish.indexOf(f),name:f.name,location:atlas.locations[spot].name,minimum:Math.ceil(f.low+(f.high-f.low)*.45)};
}
let cupBoard=null,rankPage=0;
function cupText(id,value){if($(id).textContent!==value)setUi($(id),value);}
function drawCup(){
 const goal=cupBoard?.goal||tournamentGoal(), joined=enteredCup===goal.day;
 const timing=goal.species===40?' Fish at dusk or night.':goal.species===41?' Fish at dawn or night.':'';
 if(language==='th')cupText('cupGoal',atlas.fish[goal.species].name+' · '+(g?L(readEngineText(g.measurement(goal.species,goal.minimum))):'ความยาว')+' อย่างน้อย '+goal.minimum+' ซม.'+(g?' · '+baitTip(goal.species):''));
 else cupText('cupGoal',atlas.fish[goal.species].name+' · '+goal.minimum+' cm minimum '+(g?readEngineText(g.measurement(goal.species,goal.minimum)).toLowerCase():'length')+(g?' · '+baitTip(goal.species):''));
 cupText('cupLocation',atlas.locations[goal.spot].name+' · closes at midnight, Bangkok time.'+timing);
 cupText('cupJoin',joined?'Fishing this cup':'Enter daily cup');
 $('cupJoin').disabled=joined||requestInFlight||location.protocol==='file:';
 $('cupTravel').disabled=!g||g.state()===5;
 cupText('cupScope',location.hostname.endsWith('.chatgpt.site')?'Private playtest standings':'Local host standings');
 cupText('cupMine',cupNotice||(cupBoard?.rank?cupBoard.angler+' · rank #'+cupBoard.rank+' · '+cupBoard.best+' cm':joined?(cupBoard?.angler||'Entered')+' · file a qualifying catch.':'Enter before landing your catch.'));
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
 const goal=cupBoard?.goal||tournamentGoal();
 if(!pendingDay||pendingDay!==goal.day||placeId!==goal.spot||g.species()!==goal.species||g.lengthCm()<goal.minimum)return;
 const best=cupState.pending?.day===goal.day?cupState.pending.cm:0;
 cupState.pending={action:'file',day:goal.day,spot:placeId,species:g.species(),cm:Math.max(best,g.lengthCm())};
 rememberCup();void syncCup();
}
$('cupJoin').onclick=()=>syncCup('join');
$('cupTravel').onclick=()=>{const goal=cupBoard?.goal||tournamentGoal();if(g.state()===5)return;chooseSpot(goal.spot,goal.species===40?2:goal.species===41?3:timeMode);closeMenu();};
setInterval(()=>{if(powered&&!document.hidden&&(menu.open&&menuPage==='crew'||cupState.pending))syncCup();},10000);
