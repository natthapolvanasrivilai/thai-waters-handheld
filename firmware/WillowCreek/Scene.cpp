#include "Scene.h"
#include "Connected.h"
#include "Landscape.h"
#include "FishArt.h"
#include <cstdio>
#include <cstring>
using creek::Phase;
namespace {
constexpr int ink=0x19e7,paper=0xe70f,white=0xff9b,gold=0xf50c,green=0x94f2,red=0xf386;
uint16_t* background=nullptr;
int cachedSite=-1,cachedTime=-1;
void landscape(int site,int time){
  auto fb=screen.getFramebuffer();
  for(int x=0;x<480;x++)for(int y=0;y<320;y++)fb[x*320+319-y]=colors[site][time][places[site][y*480+x]];
}
void label(int x,int y,const char* s,int col=white,int size=2){
  screen.setTextSize(size);screen.setTextColor(col);screen.setCursor(x,y);screen.print(s);
}
void fish(int x,int y,int k,int kind){
  for(int row=0;row<25;row++){
    int start=0,prev=0;
    for(int col=0;col<=48;col++){
      int packed=col==48?0:fishArt[kind][row*24+col/2];
      int c=col&1?packed&15:packed>>4;
      if(c!=prev){if(prev)screen.fillRect(x+start*k,y+row*k,(col-start)*k,k,fishInk[kind][prev]);start=col;prev=c;}
    }
  }
}
const char* wheelFault(Field f){
  switch(f){case Field::Weak:return "Magnet too weak";case Field::Strong:return "Magnet too strong";
  case Field::NoMagnet:return "Center magnet over reel sensor";default:return "Connect AS5600 reel to J8";}
}
void top(const View& v){
  screen.fillRect(0,0,480,33,ink);label(10,10,creek::destinations[v.destination].name,paper,strlen(creek::destinations[v.destination].name)>18?1:2);
  char t[50];snprintf(t,sizeof(t),"%s  %s",creek::times[v.game.timeSlot],pondClock());
  label(235,12,t,green,1);label(397,9,"MENU",gold);
}
void options(const View& v){
  const char* music[]={"Adaptive","Drift","Melody","Off"};
  const char* volume[]={"Off","Low","Medium","High"};
  const char* cues[]={"Light + tone","Light","Tone"};
  const char* rows[]={"Music","Music volume","Bite cue","Cue volume","Reel direction","Controls","Rod calibration"};
  const char* vals[]={music[v.sound.music],volume[v.sound.volume],cues[v.sound.cue],volume[v.sound.cueVolume],
    v.sound.reverse?"Reversed":"Forward",v.practice?"Touch practice":"Motion + knob","Set two poses"};
  screen.fillScreen(ink);label(14,12,"SOUND + CONTROLS",paper);label(397,12,"DONE",gold);
  for(int i=0;i<7;i++){
    int y=42+37*i;screen.drawFastHLine(14,y,450,0x428c);label(15,y+10,rows[i],white);label(258,y+10,vals[i],green);
  }
  label(14,305,v.audio?"Tap a row to change it.":"Audio unavailable - check codec.",gold,1);
}
void calibration(const View& v){
  bool rest=v.page==Page::Rest;
  screen.fillScreen(ink);label(18,17,"ROD CALIBRATION",green);label(380,17,"MENU",white);
  label(18,74,rest?"1  Playing position":"2  Raised rod",paper,3);
  label(18,137,rest?"Hold the screen as you play.":"Lift the far edge 30-50 degrees.");
  label(18,172,v.badPose?"Try a larger, steady lift.":!v.motion?"IMU unavailable. Try practice.":v.stable?"Steady. Tap to capture.":"Hold still for half a second.",gold);
  screen.fillRoundRect(16,232,448,52,6,v.stable?0x43af:0x322b);
  label(33,250,rest?"CAPTURE PLAYING POSITION":"CAPTURE RAISED POSITION");
}
void play(const View& v){
  if(cachedSite!=v.game.site||cachedTime!=v.game.timeSlot||!background){
    landscape(v.game.site,v.game.timeSlot);cachedSite=v.game.site;cachedTime=v.game.timeSlot;
    if(background)memcpy(background,screen.getFramebuffer(),480*320*2);
  }else memcpy(screen.getFramebuffer(),background,480*320*2);
  const auto& g=v.game;
  if(background){
    auto fb=screen.getFramebuffer();
    for(int y=172;y<260;y+=4){
      int shift=int(std::round(1.6f*std::sin(y*.11f+v.time*.0018f)));
      if(!shift)continue;
      for(int x=2;x<478;x++)memcpy(fb+x*320+316-y,background+(x+shift)*320+316-y,8);
    }
  }
  top(v);
  int bobX=312+int(7*std::sin(v.time*.0015f));
  int bobY=184+int(2*std::sin(v.time*.005f));
  if(g.phase==Phase::Flight){float t=creek::limit(g.age/650.f,0,1);bobX=100+int(212*t);bobY=106+int(78*t-216*t*(1-t));}
  if(g.phase==Phase::Fight){bobX=130+int(178*creek::limit(g.line/g.target,0,1));bobY=198+int(6*std::sin(v.time*.012f));}
  if(g.phase==Phase::Bite)bobY+=12;else if(g.teasing())bobY+=4;
  float tilt=creek::limit(v.degrees,-25,80);float wave=std::sin(v.time*.0024f);
  float angle=(48+tilt*.56f+1.2f*wave)*.01745329f;
  int tipX=12+int(162*std::cos(angle)),tip=248-int(162*std::sin(angle));
  int midX=(12+tipX)/2+4,midY=(248+tip)/2-5;
  for(int n=0;n<14;n++){
    int x=(n*83+int(v.time/(80+n*4)))%472,y=169+(n*19)%78;
    if(std::sin(v.time*.0015f+n)>.15)screen.drawFastHLine(x,y,3+n%7,colors[g.site][g.timeSlot][places[g.site][(y-2)*480+x]]);
  }
  if(eventActive())label(14,40,eventStatus(),white,1);
  screen.drawLine(12,246,midX,midY,ink);constexpr int rodColors[]={0x7390,0xb344,0x34f6};screen.drawLine(13,246,midX+1,midY,rodColors[v.rodFinish]);screen.drawLine(midX,midY,tipX,tip,ink);
  if(g.phase==Phase::Ready){
    int hangX=tipX+int(3*std::sin(v.time*.003f));
    screen.drawLine(tipX,tip,hangX,tip+24,0x73ee);screen.fillRect(hangX-2,tip+24,4,6,gold);
  }
  if(g.running()){
    screen.drawLine(tipX,tip,bobX,bobY,0x73ee);
    screen.fillRect(bobX-3,bobY-6,7,5,gold);screen.fillRect(bobX-3,bobY-1,7,3,white);
    screen.drawFastHLine(bobX-11,bobY+4,23,paper);
  }
  const char* head="Raise the rod";const char* sub="Then sweep forward to your playing position.";
  char desc[64];int col=white;
  switch(g.phase){
  case Phase::Ready:if(v.raised)head="Cast forward";if(v.practice){head="Tap to cast";sub="Touch practice uses the lower panel.";}break;
  case Phase::Flight:head="Casting";sub="Let the float settle.";break;
  case Phase::Waiting:head="Watch the float";sub="Wait for it to go under.";break;
  case Phase::Bite:
    if(v.sound.cue!=2){head=v.practice?"BITE!  Tap to hook":"BITE!  Lift now";sub="";col=gold;screen.drawRoundRect(bobX-18,bobY-16,36,32,7,gold);}
    else {head="Watch the float";sub="Listen for the two-note bite.";}break;
  case Phase::Fight:
    fish(bobX-68,bobY+3,2,g.fish);
    head=g.surge()?"Fish running - ease off":"Reel it in";col=g.surge()?gold:white;
    snprintf(desc,sizeof(desc),"%.1f turns left  |  %s",g.line,v.practice?"Tap for 1/4 turn":"Watch line tension");sub=desc;
    screen.fillRect(284,250,170,8,green);screen.fillRect(284,250,int(170*g.heat),8,red);break;
  case Phase::Landed:{
    const auto& f=creek::catalog[g.fish];
    fish(144,102,4,g.fish);
    screen.fillRect(0,218,480,102,ink);label(12,225,f.name,white);
    int grams=creek::weightGrams(g.fish,g.length);char mass[20];
    if(grams<1000)snprintf(mass,sizeof(mass),"%d g",grams);else snprintf(mass,sizeof(mass),"%.2f kg",grams/1000.);
    snprintf(desc,sizeof(desc),"%s   |   Length %d cm   |   Weight %s",creek::ranks[f.tier],g.length,mass);
    label(12,249,desc,gold,1);label(12,267,"ORIGIN",green,1);label(12,279,f.lore,paper,1);
    label(12,301,g.pointsAwarded?"New discovery +1 tackle point":g.newEntry?"New discovery":g.personalBest?"Personal best":"Collection updated",gold,1);
    label(358,300,v.practice?"TAP TO CAST":"CAST AGAIN",white,1);return;}
  case Phase::Lost:
    head=g.reason==creek::Reason::Early?"Hook set too early":g.reason==creek::Reason::Late?"The bite passed":g.reason==creek::Reason::Snapped?"The line snapped":"The fish slipped away";
    sub=v.practice?"Tap to cast again.":"Raise and cast again.";break;
  }
  if(!v.practice && (!v.motion || v.field!=Field::Good)){
    head=!v.motion?"Check the motion sensor":wheelFault(v.field);sub="Paused. Menu offers touch practice.";col=gold;
  }
  screen.fillRect(0,264,480,56,ink);label(12,271,head,col);label(12,298,sub,green,1);
}
}
void beginScene(){
  if(!screenOK)return;
  background=(uint16_t*)ps_malloc(480*320*2);

}
namespace {
using namespace creek;
void bar(const char* title){
 screen.fillScreen(ink);label(12,11,title,paper);label(400,11,"BACK",gold);screen.drawFastHLine(10,36,460,green);
}
void row(int y,const char* title,const char* value){
 label(14,y,title,white);label(278,y,value,gold);screen.drawFastHLine(12,y+22,452,0x428c);
}
void hub(const View& v){
 bar("THAI WATERS");
 const char* a[]={"Fishing spots","Fish collection","Rod workshop","Bench test","Sound + controls","Touch practice"};
 const char* b[]={sites[v.game.site].water,"Collection",chapters[v.game.progress.chapter()],"Live readings","Settings",v.practice?"On":"Off"};
 for(int i=0;i<6;i++)row(53+i*41,a[i],b[i]);
 label(14,295,"Wi-Fi + clock",white);label(278,295,"Updates",gold);
}
void waters(const View& v){
 bar("FISHING SPOTS");
 for(int i=0;i<4;i++){
   int id=v.spotPage*4+i;if(id>=destinationCount)break;int y=49+42*i;
   const auto& spot=destinations[id];label(16,y,spot.name,id==v.pendingSite?gold:white,strlen(spot.name)>33?1:2);
   char first[76]{};size_t split=std::min<size_t>(74,strlen(spot.story));
   if(spot.story[split])while(split&&spot.story[split]!=' ')--split;
   memcpy(first,spot.story,split);label(16,y+16,first,green,1);
   if(spot.story[split])label(16,y+26,spot.story+split+1,green,1);
 }
 for(int i=0;i<5;i++)label(i*96+9,230,i==4?"Live":times[i],i==v.pendingTime?gold:white);
 label(15,285,"< PREV",gold);screen.fillRoundRect(110,272,254,39,5,0x336b);label(176,285,"FISH HERE",white);label(390,285,"NEXT >",gold);
}
void book(const View& v){
 const auto& journal=v.game.progress.book;int site=v.bookPage/2,start=(v.bookPage%2)*6;char buf[85];
 bar("FISH COLLECTION");snprintf(buf,sizeof(buf),"%s   %d/%d",sites[site].name,journal.discovered(),fishCount);label(14,48,buf,gold);
 for(int k=start;k<std::min(start+6,stockSize(site));k++){
   int id=stockId(site,k);const auto& e=journal.entries[id];int y=75+33*(k-start);
   label(14,y,catalog[id].name,e.count?white:green);
   if(e.count)snprintf(buf,sizeof(buf),"%s | %lu caught | best %u cm",ranks[catalog[id].tier],(unsigned long)e.count,(unsigned)e.best);
   else snprintf(buf,sizeof(buf),"%s | %s",ranks[catalog[id].tier],id==prawn?"Dusk ferry piles - lift quickly":id==ray?"Night sandbars - ease off on long runs":times[id%4]);label(14,y+17,buf,paper,1);
 }
 label(16,288,"< PREV",gold);snprintf(buf,sizeof(buf),"%d / 10",v.bookPage+1);label(205,288,buf);label(372,288,"NEXT >",gold);
}
void network(){
 bar("WI-FI + CLOCK");label(14,48,networkStatus(),white,1);label(14,68,updateStatus(),green,1);
 label(14,90,setupName(),gold);label(14,115,setupCode(),paper,1);label(14,132,pondClock(),white);
 row(167,"Phone setup","Start");row(212,"Online update","Check");row(257,"Wi-Fi radio",radioEnabled()?"On":"Off");
 label(14,289,"Shared event",white);label(176,292,eventStatus(),green,1);
}
void journey(const View& v){
 const auto& p=v.game.progress;char buf[72];bar("ROD WORKSHOP");
 snprintf(buf,sizeof(buf),"%s  |  %d points",chapters[p.chapter()],p.points());label(14,49,buf,gold);
 label(14,71,letters[p.chapter()],paper,1);label(14,85,story[p.chapter()],white,1);
 const char* units[]={"+150 ms per rank","+12% retrieval per rank","-10% tension gain per rank"};
 for(int i=0;i<3;i++){
   int y=104+48*i;label(16,y,paths[i]);snprintf(buf,sizeof(buf),"Rank %d/3",p.rank[i]);label(293,y,buf,green);
   snprintf(buf,sizeof(buf),"%s   /   next cost %d",units[i],p.rank[i]+1);label(16,y+20,p.rank[i]==3?"Maximum rank":buf,paper,1);
 }
 label(14,252,"ROD FINISH",green,1);label(14,267,finishes[v.rodFinish],white);label(252,264,v.refundConfirm?"Confirm refund":"Refund points",gold);
 label(14,298,v.notice,green,1);
}
void bench(const View& v){
 bar("BENCH TEST");char b[90];
 snprintf(b,sizeof(b),"Tilt %+.1f deg   lift %.1f / low %.1f",v.degrees,v.span*.70,v.span*.27);
 label(12,46,v.calibrated&&v.motion?b:v.motion?"Calibrate two poses for degrees":"IMU unavailable",paper);
 snprintf(b,sizeof(b),"Casts %lu   Lifts %lu",(unsigned long)v.casts,(unsigned long)v.lifts);label(12,76,b);
 snprintf(b,sizeof(b),"%s | acceleration %.2f g",v.benchEvent,v.accelG);label(12,99,b,green,1);
 snprintf(b,sizeof(b),"Raw %d   %+.2f turns",v.raw,v.turns);label(12,123,v.field==Field::Good?b:wheelFault(v.field),gold);
 label(12,148,v.field!=Field::Good?"Reel paused":v.direction>0?"Winding IN":v.direction<0?"Paying OUT":"Turn the knob",white);
 label(12,175,v.sound.reverse?"Reverse direction: ON":"Reverse direction: OFF",green);
 snprintf(b,sizeof(b),"Cue level %d/3",v.sound.cueVolume);label(12,209,b,gold);label(251,209,"PLAY BITE",white);
 snprintf(b,sizeof(b),"Rumble %d/3",v.rumble);label(12,246,b,gold);label(177,246,"Tease",white);label(286,246,"Bite",white);label(387,246,"Pull",white);
 label(12,279,v.driver?"DRV2605L detected":"No DRV2605L detected",green,1);
 label(12,301,v.audio?"Tap a level to cycle. Tap direction to reverse.":"Audio unavailable - inspect codec / speaker.",paper,1);
}
}
void paint(const View& v){
 if(!screenOK)return;
 switch(v.page){
 case Page::Play:play(v);break;case Page::Hub:hub(v);break;case Page::Waters:waters(v);break;
 case Page::Book:book(v);break;case Page::Journey:journey(v);break;case Page::Bench:bench(v);break;
 case Page::Network:network();break;case Page::Options:options(v);break;default:calibration(v);break;
 }
 if(v.saveFailed){screen.fillRect(0,302,480,18,ink);label(12,305,"Journal save failed - keep power on and check storage.",red,1);}
 screen.flush();
}

