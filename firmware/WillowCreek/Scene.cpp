#include "Scene.h"
#include "LcdGlyphs.h"
#include "RodFeedback.h"
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
static_assert(sizeof(scenery::recipes)/sizeof(scenery::recipes[0])==creek::destinationCount,"Missing scenic recipe");
void landscape(int place,int time){
  auto fb=screen.getFramebuffer();
  auto indexed=reinterpret_cast<uint8_t*>(fb);
  scenery::Color colors[scenery::colorCount]{};
  uint16_t lcd[scenery::colorCount];
  scenery::render({indexed},colors,place,time);
  for(int i=0;i<scenery::colorCount;i++){
    auto c=colors[i];lcd[i]=uint16_t(((c>>8)&0xf800)|((c>>5)&0x07e0)|((c>>3)&31));
  }
  // Expand backwards so the 2x RGB565 output only overwrites indices already read.
  for(int x=scenery::width-1;x>=0;x--)for(int y=scenery::height-1;y>=0;y--){
    uint16_t color=lcd[indexed[x*scenery::height+y]];
    int dest=2*x*320+2*y;
    fb[dest]=fb[dest+1]=fb[dest+320]=fb[dest+321]=color;
  }
}
const lcdtype::Face& fontFace(int size){
  return size>=3?lcdtype::title:size==2?lcdtype::body:lcdtype::caption;
}
const lcdtype::Glyph& glyph(const lcdtype::Face& face,unsigned char c){
  return face.glyphs[(c>=32 && c<=126?c:'?')-32];
}
int textWidth(const char* text,int size){
  const auto& face=fontFace(size);int width=0;
  for(;*text;++text)width+=glyph(face,*text).advance;
  return width;
}
uint16_t blendText(uint16_t bg,uint16_t fg,unsigned alpha){
  if(alpha==3)return fg;
  const unsigned back=3-alpha;
  unsigned r=((bg>>11)*back+(fg>>11)*alpha+1)/3;
  unsigned g=(((bg>>5)&63)*back+((fg>>5)&63)*alpha+1)/3;
  unsigned b=((bg&31)*back+(fg&31)*alpha+1)/3;
  return uint16_t((r<<11)|(g<<5)|b);
}
void label(int x,int y,const char* text,int color=white,int size=2,int right=480){
  const auto& face=fontFace(size);auto fb=screen.getFramebuffer();
  for(;*text;++text){
    const auto& g=glyph(face,*text);
    if(x+g.advance>right)break;
    for(int j=0;j<g.h;++j){
      int py=y+g.top+j;if(py<0||py>=320)continue;
      for(int i=0;i<g.w;++i){
        const int px=x+g.left+i;
        if(px<0||px>=right||px>=480)continue;
        const int n=j*g.w+i;
        const unsigned coverage=(face.pixels[g.offset+n/4]>>(6-2*(n%4)))&3;
        if(coverage){auto& dst=fb[px*320+319-py];dst=blendText(dst,color,coverage);}
      }
    }
    x+=g.advance;
  }
}
void fish(int x,int y,float k,int kind){
  for(int row=0;row<25;row++){
    int start=0,prev=0;
    for(int col=0;col<=48;col++){
      int packed=col==48?0:fishArt[kind][row*24+col/2];
      int c=col&1?packed&15:packed>>4;
      if(c!=prev){if(prev)screen.fillRect(x+int(start*k),y+int(row*k),int(col*k)-int(start*k),int((row+1)*k)-int(row*k),fishInk[kind][prev]);start=col;prev=c;}
    }
  }
}
const char* wheelFault(Field f){
  switch(f){case Field::Weak:return "Magnet too weak";case Field::Strong:return "Magnet too strong";
  case Field::NoMagnet:return "Center magnet over reel sensor";default:return "Connect AS5600 reel to J8";}
}
void batteryIcon(int x,int y,const BatteryReading& b){
  int color=b.percent>=0 && b.percent<=15 && !b.charging?red:paper;
  screen.drawRect(x,y,17,9,color);screen.fillRect(x+17,y+2,2,5,color);
  if(b.percent>=0)screen.fillRect(x+2,y+2,(13*b.percent+50)/100,5,color);
  char text[12];
  if(b.percent>=0)snprintf(text,sizeof(text),"%s%d%%",b.charging?"+":"",b.percent);
  else snprintf(text,sizeof(text),"%s",b.valid&&!b.present&&b.usb?"USB":"--");
  label(x+22,y+1,text,color,1);
}
void tensionLight(float tension){
  const int n=std::min(8,std::max(0,int(std::ceil(tension*8))));
  const int color=tension>=.8f?red:tension>=.55f?gold:green;
  screen.fillRoundRect(464,104,13,110,4,ink);
  for(int i=0;i<8;i++)screen.fillRect(467,201-i*13,7,9,i<n?color:0x428c);
  if(tension>=.8f){screen.fillRect(438,90,39,12,ink);label(445,92,"EASE",gold,1);}
}
void top(const View& v){
  screen.fillRect(0,0,480,33,ink);label(10,10,creek::destinations[v.destination].name,paper,strlen(creek::destinations[v.destination].name)>18?1:2);
  char t[50];snprintf(t,sizeof(t),"%s  %s",creek::times[v.game.timeSlot],pondClock());
  label(229,12,strstr(t,"needs sync")?"Clock needs sync":t,green,1);batteryIcon(332,11,v.battery);label(404,9,"MENU",gold);
}
void menuText(int x,int y,const char* text,int color=white,int size=2,int width=0){
  int available=width?width:menuui::w-x-8;
  if(size==2 && textWidth(text,size)>available)size=1;
  label(menuui::x+x,menuui::y+y,text,color,size,menuui::x+x+available);
}
void menuHeader(const char* title,const char* action="BACK"){
  auto fb=screen.getFramebuffer();
  // RGB565 channel-aligned arithmetic. Retain one quarter of the actual scene.
  for(int x=0;x<menuui::w;x++)for(int y=0;y<menuui::h;y++){
    int dx=std::min(x,menuui::w-1-x),dy=std::min(y,menuui::h-1-y);
    if(dx<6&&dy<6&&(6-dx)*(6-dx)+(6-dy)*(6-dy)>36)continue;
    auto& pixel=fb[(menuui::x+x)*320+319-(menuui::y+y)];
    pixel=((pixel&0xe79c)>>2)+((ink&0xf7de)>>1)+((ink&0xe79c)>>2);
  }
  screen.drawRoundRect(menuui::x,menuui::y,menuui::w,menuui::h,7,0x6bf0);
  menuText(12,10,title,paper);
  menuText(menuui::w-58,12,action,gold,1);
  screen.drawFastHLine(menuui::x+8,menuui::y+menuui::header-1,menuui::w-16,0x526d);
}
void menuRow(int y,int height,const char* name,const char* value){
  menuText(12,y+(height-14)/2,name,white,2,204);
  menuText(220,y+(height-14)/2,value,gold,2,164);
  screen.drawFastHLine(menuui::x+10,menuui::y+y+height-1,menuui::w-20,0x426a);
}
void options(const View& v){
  const char* music[]={"Adaptive","Drift","Melody","Off"};
  const char* volume[]={"Off","Low","Medium","High"};
  const char* cues[]={"Light + tone","Light","Tone"};
  const char* rows[]={"Music","Music volume","Bite cue","Cue volume","Reel direction","Controls","Rod calibration","Reel click"};
  const char* vals[]={music[v.sound.music],volume[v.sound.volume],cues[v.sound.cue],volume[v.sound.cueVolume],
    v.sound.reverse?"Reversed":"Forward",v.practice?"Touch practice":"Motion + knob","Set two poses",volume[v.sound.reelVolume]};
  menuHeader("SOUND + CONTROLS");
  for(int i=0;i<8;i++)menuRow(menuui::header+i*menuui::optionRow,menuui::optionRow,rows[i],vals[i]);
  if(!v.audio)menuText(12,259,"Audio unavailable - check codec.",gold,1);
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
void waterStrike(int x,int y,uint32_t age,bool surge){
  const int period=surge?390:690;
  for(int i=0;i<2;i++){
    float t=((age+i*period/2)%period)/float(period);
    int wide=5+int(18*t),high=2+int(4*t);
    screen.drawEllipse(x,y,wide,high,i?0xa637:0xe73b);
    int lift=int((surge?16:9)*4*t*(1-t));
    screen.fillRect(x+(i?1:-1)*(3+int(t*17)),y-lift-3,3,2,0xffff);
  }
}
void collectionMark(uint32_t age){
  const int x=447,y=59;bool arriving=age>=2400 && age<3000;
  screen.fillRoundRect(x-26,y-12,55,28,4,ink);
  int edge=arriving?gold:white;
  screen.drawRect(x-9,y-7,9,11,edge);screen.drawRect(x,y-7,9,11,edge);
  label(x-21,y+6,"Journal",edge,1);
}
void play(const View& v){
  if(cachedSite!=v.destination||cachedTime!=v.game.timeSlot||!background){
    landscape(v.destination,v.game.timeSlot);cachedSite=v.destination;cachedTime=v.game.timeSlot;
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
  if(v.page==Page::Play)top(v);
  int bobX=312+int(7*std::sin(v.time*.0015f));
  int bobY=184+int(2*std::sin(v.time*.005f));
  if(g.phase==Phase::Flight){float t=creek::limit(g.age/650.f,0,1);bobX=100+int(212*t);bobY=106+int(78*t-216*t*(1-t));}
  if(g.phase==Phase::Fight){
    bobX=130+int(178*creek::limit(g.line/g.target,0,1)+g.pullOffset());
    float drift=g.holdingBottom()?0.f:g.fightStyle()==creek::FightStyle::Picker?2.f:8.f;
    bobY=195+int(drift*std::sin(g.age*.006f));
  }
  if(g.phase==Phase::Waiting && g.rig==creek::Technique::Spoon)bobX-=int(30*(g.strokes+g.lureTurns));
  if(g.phase==Phase::Waiting && g.rig==creek::Technique::Jig && g.falling)bobY-=int(28*(1-creek::limit((g.age-g.fallStart)/780.f,0,1)));
  if(g.phase==Phase::Bite)bobY+=12;else if(g.teasing())bobY+=4;
  float tilt=creek::limit(v.degrees,-25,80);float wave=std::sin(v.time*.0024f);
  float angle=(48+tilt*.56f+1.2f*wave)*.01745329f;
  const float reach=162*std::cos(angle),rise=162*std::sin(angle),load=g.rodLoad();
  const float sideways=.20f*g.pullOffset();
  int tipX=12,tip=248;
  for(int n=0;n<14;n++){
    int x=(n*83+int(v.time/(80+n*4)))%472,y=169+(n*19)%78;
    if(std::sin(v.time*.0015f+n)>.15)screen.drawFastHLine(x,y,3+n%7,screen.getFramebuffer()[x*320+319-(y-2)]);
  }
  if(v.page==Page::Play && eventActive())label(14,40,eventStatus(),white,1);
  constexpr int rodColors[]={0x7390,0xb344,0x34f6};
  for(int section=1;section<=5;section++){
    float t=section*.2f,flex=load*t*t*t;
    int x=12+int(reach*t+11*flex+sideways*t*t*t),y=248-int(rise*t-41*flex+4*t*(1-t));
    screen.drawLine(tipX,tip,x,y,ink);
    if(section<5)screen.drawLine(tipX+1,tip,x+1,y,rodColors[v.rodFinish]);
    tipX=x;tip=y;
  }
  if(g.phase==Phase::Ready){
    int hangX=tipX+int(3*std::sin(v.time*.003f));
    screen.drawLine(tipX,tip,hangX,tip+24,0x73ee);screen.fillRect(hangX-2,tip+24,4,6,gold);
  }
  if(g.running()){
    screen.drawLine(tipX,tip,bobX,bobY,0x73ee);
    if(g.phase!=Phase::Fight){if(g.rig==creek::Technique::Float){screen.fillRect(bobX-3,bobY-6,7,5,gold);screen.fillRect(bobX-3,bobY-1,7,3,white);}
    else {bool jig=g.rig==creek::Technique::Jig;screen.fillRect(bobX-2,bobY-3,jig?4:10,jig?9:4,white);screen.fillRect(bobX-2,bobY-3,4,3,gold);}
    screen.drawFastHLine(bobX-11,bobY+4,23,paper);}
  }
  if(v.page!=Page::Play)return;
  const char* head="Raise the rod";const char* sub="Then sweep forward to your playing position.";
  char desc[64];int col=white;
  switch(g.phase){
  case Phase::Ready:if(v.raised)head="Cast forward";if(v.practice){head="Tap to cast";sub="Touch practice uses the lower panel.";}break;
  case Phase::Flight:head="Casting";sub="Let the float settle.";break;
  case Phase::Waiting:
    if(g.rig==creek::Technique::Float)head=g.teasing()?"Nibble - hold steady":"Watch the float";
    else if(g.rig==creek::Technique::Spoon)head=g.falling?"Pause - let the spoon flutter":v.practice?"Tap 3 times to wind":"Wind a short burst";
    else head=g.falling?(g.rodHeldHigh?"Lower the rod":"Let the jig fall"):v.practice?"Tap to work the jig":"Lift the jig, then lower";
    break;
  case Phase::Bite:
    if(v.sound.cue!=2){head=v.practice?"BITE!  Tap to hook":"BITE!  Lift now";sub="";col=gold;screen.drawRoundRect(bobX-18,bobY-16,36,32,7,gold);}
    else {head="Listen to the line";sub="Listen for the two-note bite.";}break;
  case Phase::Fight:
    if(g.holdingBottom()||g.fightStyle()==creek::FightStyle::Picker){
      int radius=g.holdingBottom()?5+(g.age%1300)/85:3+int(10*load);
      screen.drawEllipse(bobX,bobY,radius,2+radius/5,0xe73b);
    }else waterStrike(bobX,bobY,g.age,g.surge());
    head=creek::fightInstruction(g);col=g.surge()?gold:white;
    snprintf(desc,sizeof(desc),"%.1f turns left  |  %s",g.line,v.practice?"Tap for 1/4 turn":"Watch line tension");sub=desc;
    break;
  case Phase::Landed:{
    const auto& f=creek::catalog[g.fish];
    collectionMark(g.age);
    float t=creek::limit((int(g.age)-1600)/800.f,0,1);
    float ease=t*t*(3-2*t),k=3.7f-3.4f*ease;
    if(t<1){
      int cx=240+int(207*ease),cy=136-int(77*ease+46*4*t*(1-t));
      fish(cx-int(24*k),cy-int(12.5f*k),k,g.fish);
    }
    int grams=creek::weightGrams(g.fish,g.length);char mass[22];
    if(grams<1000)snprintf(mass,sizeof(mass),"%d g",grams);else snprintf(mass,sizeof(mass),"%.2f kg",grams/1000.);
    snprintf(desc,sizeof(desc),"%s  /  %d cm  /  %s",creek::ranks[f.tier],g.length,mass);
    int w=std::max(strlen(f.name)*12,strlen(desc)*6)+16;
    screen.fillRoundRect((480-w)/2,192,w,37,4,ink);
    label((480-textWidth(f.name,2))/2,197,f.name,white);
    label((480-textWidth(desc,1))/2,216,desc,gold,1);
    screen.fillRoundRect(7,287,textWidth(f.lore,1)+12,16,3,ink);label(13,291,f.lore,paper,1);
    if(t>=1)label(14,306,g.pointsAwarded?"Collection +1 tackle point":"Catch recorded",white,1);
    return;}
  case Phase::Lost:
    head=g.reason==creek::Reason::Early?"Hook set too early":g.reason==creek::Reason::Late?"The bite passed":g.reason==creek::Reason::Snapped?"The line snapped":g.reason==creek::Reason::Unworked?"The fish lost interest":"The fish slipped away";
    sub=v.practice?"Tap to cast again.":"Raise and cast again.";break;
  }
  if(!v.practice && (!v.motion || v.field!=Field::Good)){
    head=!v.motion?"Check the motion sensor":wheelFault(v.field);sub="Paused. Menu offers touch practice.";col=gold;
  }
  char hint[96];snprintf(hint,sizeof(hint),"%s",head);
  if(g.phase==Phase::Fight)snprintf(hint,sizeof(hint),"%s  %.1f turns",head,g.line);
  if(!v.practice&&(!v.motion||v.field!=Field::Good))snprintf(hint,sizeof(hint),"%s",head);
  int width=12+textWidth(hint,1);
  screen.fillRoundRect(7,296,width,17,3,ink);label(13,301,hint,col,1);
  if(g.phase==Phase::Fight)tensionLight(g.heat);
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
void hub(const View& v){
 menuHeader("THAI WATERS","RESUME");
 const char* names[]={"Fishing spots","Fish collection","Rod workshop","Bench test","Sound + controls","Touch practice","Wi-Fi + clock"};
 const char* values[]={sites[v.game.site].water,"Collection",chapters[v.game.progress.chapter()],"Live readings","Settings",v.practice?"On":"Off","Updates"};
 for(int i=0;i<7;i++)menuRow(menuui::header+i*menuui::hubRow,menuui::hubRow,names[i],values[i]);
}
void waters(const View& v){
 menuHeader("FISHING SPOTS");
 for(int i=0;i<4;i++){
   int id=v.spotPage*4+i;if(id>=destinationCount)break;
   int y=menuui::header+menuui::waterRow*i;
   const auto& spot=destinations[id];
   if(id==v.pendingSite)screen.fillRect(menuui::x+4,menuui::y+y+3,3,menuui::waterRow-5,gold);
   menuText(12,y+2,spot.name,id==v.pendingSite?gold:white);
   constexpr int columns=(menuui::w-24)/6;
   char first[columns+1]{};size_t split=std::min<size_t>(columns,strlen(spot.story));
   if(spot.story[split])while(split&&spot.story[split]!=' ')--split;
   memcpy(first,spot.story,split);menuText(12,y+17,first,paper,1);
   if(spot.story[split])menuText(12,y+25,spot.story+split+1,paper,1);
 }
 for(int i=0;i<5;i++){
   int left=i*menuui::w/5;
   if(i==v.pendingTime)screen.drawRect(menuui::x+left+4,menuui::y+menuui::periodY,menuui::w/5-8,29,gold);
   menuText(left+10,menuui::periodY+10,i==4?"Live":times[i],i==v.pendingTime?gold:white,1);
 }
 menuText(12,menuui::travelY+12,"< PREV",gold,1);
 screen.fillRoundRect(menuui::x+menuui::w/4,menuui::y+menuui::travelY,menuui::w/2,32,5,0x336b);
 menuText(140,menuui::travelY+8,"FISH HERE");menuText(340,menuui::travelY+12,"NEXT >",gold,1);
}
void book(const View& v){
 const auto& journal=v.game.progress.book;int site=v.bookPage/2,start=(v.bookPage%2)*6;char buf[85];
 menuHeader("FISH COLLECTION");snprintf(buf,sizeof(buf),"%s   %d/%d",sites[site].name,journal.discovered(),fishCount);menuText(12,38,buf,gold,1);
 for(int k=start;k<std::min(start+6,stockSize(site));k++){
   int id=stockId(site,k);const auto& e=journal.entries[id];int y=56+29*(k-start);
   menuText(12,y,catalog[id].name,e.count?white:green);
   if(e.count)snprintf(buf,sizeof(buf),"%s | %lu caught | best %u cm",ranks[catalog[id].tier],(unsigned long)e.count,(unsigned)e.best);
   else snprintf(buf,sizeof(buf),"%s | %s",ranks[catalog[id].tier],id==prawn?"Dusk ferry piles - lift quickly":id==ray?"Night sandbars - ease off on long runs":times[id%4]);
   menuText(12,y+16,buf,paper,1);
 }
 menuText(12,menuui::bookNav+12,"< PREV",gold,1);snprintf(buf,sizeof(buf),"%d / 10",v.bookPage+1);menuText(170,menuui::bookNav+10,buf);menuText(340,menuui::bookNav+12,"NEXT >",gold,1);
}
void network(){
 menuHeader("WI-FI + CLOCK");menuText(12,38,networkStatus(),white,1);menuText(12,53,updateStatus(),green,1);
 menuText(12,72,setupName(),gold);menuText(12,94,setupCode(),paper,1);menuText(12,111,pondClock());
 menuRow(138,31,"Phone setup","Start");menuRow(169,31,"Online update","Check");
 menuRow(200,31,"Wi-Fi radio",radioEnabled()?"On":"Off");menuRow(231,31,"Shared event",eventActive()?"Joined":"Join");
 menuText(12,263,eventStatus(),green,1);
}
void journey(const View& v){
 const auto& p=v.game.progress;char buf[80];menuHeader("ROD WORKSHOP");
 snprintf(buf,sizeof(buf),"%s  |  %d points",chapters[p.chapter()],p.points());menuText(12,37,buf,gold,1);
 snprintf(buf,sizeof(buf),"Technique   %s  >",techniques[int(v.game.rig)]);
 menuText(12,menuui::rigY+4,buf,white);
 menuText(12,80,story[p.chapter()],green,1);
 const char* units[]={"+150 ms per rank","+12% retrieval per rank","-10% tension gain per rank"};
 for(int i=0;i<3;i++){
   int y=menuui::upgradeY+i*menuui::upgradeRow;
   menuText(12,y+3,paths[i]);snprintf(buf,sizeof(buf),"Rank %d/3",p.rank[i]);menuText(272,y+3,buf,green);
   snprintf(buf,sizeof(buf),"%s / next cost %d",units[i],p.rank[i]+1);menuText(12,y+20,p.rank[i]==3?"Maximum rank":buf,paper,1);
 }
 menuText(12,menuui::finishY,"ROD FINISH",green,1);menuText(12,menuui::finishY+15,finishes[v.rodFinish],white);
 menuText(210,menuui::finishY+15,v.refundConfirm?"Confirm refund":"Refund points",gold);
 menuText(12,251,v.notice,green,1);
}
void bench(const View& v){
 bar("BENCH TEST");batteryIcon(321,15,v.battery);char b[90];
 snprintf(b,sizeof(b),"Tilt %+.1f deg   lift %.1f / low %.1f",v.degrees,v.span*.70,v.span*.27);
 label(12,46,v.calibrated&&v.motion?b:v.motion?"Calibrate two poses for degrees":"IMU unavailable",paper);
 snprintf(b,sizeof(b),"Casts %lu   Lifts %lu",(unsigned long)v.casts,(unsigned long)v.lifts);label(12,76,b);
 snprintf(b,sizeof(b),"%s | acceleration %.2f g",v.benchEvent,v.accelG);label(12,99,b,green,1);
 snprintf(b,sizeof(b),"Raw %d   %+.2f turns",v.raw,v.turns);label(12,123,v.field==Field::Good?b:wheelFault(v.field),gold);
 label(12,148,v.field!=Field::Good?"Reel paused":v.direction>0?"Winding IN":v.direction<0?"Paying OUT":"Turn the knob",white);
 label(12,175,v.sound.reverse?"Reverse direction: ON":"Reverse direction: OFF",green);
 snprintf(b,sizeof(b),"Cue level %d/3",v.sound.cueVolume);label(12,209,b,gold);label(251,209,"PLAY BITE",white);
 snprintf(b,sizeof(b),"Rumble %d/3",v.rumble);label(12,246,b,gold);label(177,246,"Tease",white);label(286,246,"Bite",white);label(387,246,"Pull",white);
 label(12,279,"Prawn pick",green);label(170,279,"Bottom hold",green);label(333,279,"Fast run",green);
 label(12,304,v.driver?"DRV2605L detected":"No DRV2605L detected",green,1);
 label(290,304,"TEST TOUCH GRID >",gold,1);
}
void touchCheck(const View& v){
 screen.fillScreen(ink);
 label(119,63,"Touch panel test",white,2);
 char status[64];snprintf(status,sizeof(status),"%u/9   Last contact %d, %d",unsigned(v.touchStep),v.lastTouchX,v.lastTouchY);
 label(130,94,status,paper,1);
 label(110,117,v.touchStep==9?"PASS - all nine targets reached":"Tap the gold cross, then lift.",gold,1);
 for(int i=0;i<9;i++){
   const int x=touchColumn[i%3],y=touchRow[i/3],col=i<v.touchStep?green:i==v.touchStep?gold:0x52aa;
   screen.drawRect(x-12,y-12,25,25,col);screen.drawLine(x-6,y,x+6,y,col);screen.drawLine(x,y-6,x,y+6,col);
 }
 screen.drawRect(52,284,101,31,paper);label(68,294,"BACK",paper,1);
}
}
void paint(const View& v){
 if(!screenOK)return;
 if(menuui::overlay(v.page))play(v);
 switch(v.page){
 case Page::Play:play(v);break;case Page::Hub:hub(v);break;case Page::Waters:waters(v);break;
 case Page::Book:book(v);break;case Page::Journey:journey(v);break;case Page::Bench:bench(v);break;
 case Page::TouchCheck:touchCheck(v);break;
 case Page::Network:network();break;case Page::Options:options(v);break;default:calibration(v);break;
 }
 if(v.saveFailed){screen.fillRect(0,302,480,18,ink);label(12,305,"Journal save failed - keep power on and check storage.",red,1);}
 screen.flush();
}

