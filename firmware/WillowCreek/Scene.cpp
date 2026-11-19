#include "Scene.h"
#include "ArrivalPixels.h"
#include "LcdGlyphs.h"
#include "WaterArt.h"
#include "RodFeedback.h"
#include "Connected.h"
#include "AmbientLcd.h"
#include "FishArt.h"
#include <cstdio>
#include <cstring>
#include <sys/time.h>
using creek::Phase;
namespace {
constexpr int ink=0x19e7,paper=0xe70f,white=0xff9b,gold=0xf50c,green=0x94f2,red=0xf386;
uint16_t* background=nullptr;
uint16_t lcd[scenery::colorCount]{};
scenery::Layout scenicLayout{};
int cachedSite=-1,cachedTime=-1,cachedWeather=-1;
static_assert(sizeof(scenery::recipes)/sizeof(scenery::recipes[0])==creek::destinationCount,"Missing scenic recipe");
void landscape(int place,int time,creek::Weather weather){
  auto fb=screen.getFramebuffer();
  auto indexed=reinterpret_cast<uint8_t*>(fb);
  scenery::Color colors[scenery::colorCount]{};
  scenery::render({indexed},colors,place,time,&scenicLayout);
  for(auto& color:colors)color=creek::weatherTint(color,weather);
  scenery::lcdPalette(colors,lcd);
  // Expand backwards so the 2x RGB565 output only overwrites indices already read.
  for(int x=scenery::width-1;x>=0;x--)for(int y=scenery::height-1;y>=0;y--){
    uint16_t color=lcd[indexed[x*scenery::height+y]];
    int dest=2*x*320+2*y;
    fb[dest]=fb[dest+1]=fb[dest+320]=fb[dest+321]=color;
  }
}
void landscapeMotion(const View& v){
  uint32_t ms=v.time;
  unsigned utcDayPlusOne=0;
  if(v.timeMode==4){
    timeval utc{};
    if(gettimeofday(&utc,nullptr)==0&&utc.tv_sec>=1735689600){
      ms=uint32_t(utc.tv_sec)*1000u+uint32_t(utc.tv_usec)/1000u;
      utcDayPlusOne=uint32_t(utc.tv_sec%86400)*1000u+uint32_t(utc.tv_usec)/1000u+1;
    }
  }
  auto frame=screen.getFramebuffer();
  scenery::LcdSpans spans{frame,background?background:frame,lcd};
  scenery::paintAmbient(spans,scenicLayout,ms,utcDayPlusOne);
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
void drawWaterProp(int kind,int x,int y,int scale=1){
  if(kind<0 || kind>=7)return;
  for(int row=0;row<9;++row){
    const char* text=waterart::marks[kind][row];
    for(int pos=0;text[pos];){
      const char ch=text[pos];int end=pos+1;
      while(text[end]==ch)++end;
      if(ch!='.'){
        const int color=ch>='a'?10+ch-'a':ch-'0';
        screen.fillRect(x+(pos-10)*scale,y+(row-4)*scale,(end-pos)*scale,scale,waterart::colors[color]);
      }
      pos=end;
    }
  }
}
void fish(int x,int y,float k,int kind){
  kind=creek::artForSpecies[kind];k*=.5f;
  for(int row=0;row<50;row++){
    int start=0,prev=0;
    for(int col=0;col<=96;col++){
      int packed=col==96?0:fishArt[kind][row*48+col/2];
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
  const int color=b.percent>=0 && b.percent<=15 && !b.charging?red:white;
  screen.fillRoundRect(x-1,y-1,26,14,4,ink);
  screen.drawRoundRect(x,y,24,12,3,color);
  screen.drawRoundRect(x+1,y+1,22,10,2,color);
  screen.fillRect(x+25,y+4,2,4,color);
  if(b.percent>=0){
    const int filled=std::min(4,(b.percent+24)/25);
    for(int i=0;i<4;i++)screen.fillRect(x+3+5*i,y+3,4,6,i<filled?color:0x5b4c);
    if(b.charging){
      screen.drawLine(x+14,y+1,x+9,y+6,ink);screen.drawFastHLine(x+9,y+6,6,ink);
      screen.drawLine(x+14,y+6,x+10,y+11,ink);
      screen.drawLine(x+14,y,x+9,y+5,gold);screen.drawFastHLine(x+9,y+5,6,gold);
      screen.drawLine(x+14,y+5,x+10,y+10,gold);
    }
  }else label(x+4,y+1,b.valid&&!b.present&&b.usb?"USB":"?",color,1);
}
void tensionLight(float tension){
  const int n=std::min(8,std::max(0,int(std::ceil(tension*8))));
  const int color=tension>=.8f?red:tension>=.55f?gold:green;
  screen.fillRoundRect(464,104,13,110,4,ink);
  for(int i=0;i<8;i++)screen.fillRect(467,201-i*13,7,9,i<n?color:0x428c);
  if(tension>=.8f){screen.fillRect(438,90,39,12,ink);label(445,92,"EASE",gold,1);}
}
void skyLabel(int x,int y,const char* text,int color,int size,int right=480){
  label(x-1,y,text,ink,size,right);label(x+1,y,text,ink,size,right);
  label(x,y-1,text,ink,size,right);label(x,y+1,text,ink,size,right);
  label(x,y,text,color,size,right);
}
void top(const View& v){
  const auto* name=creek::destinations[v.destination].name;
  skyLabel(10,10,name,white,strlen(name)>18?1:2,225);
  char t[50];snprintf(t,sizeof(t),"%s  %s",creek::times[v.game.timeSlot],pondClock());
  skyLabel(229,12,strstr(t,"needs sync")?"Clock needs sync":t,white,1,361);
  batteryIcon(365,10,v.battery);skyLabel(404,9,"MENU",gold,2);
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
// Wrap against actual glyph advances in the 264-pixel catch-details column.
int catchLines(const char* text,int y,int color,int size,int step){
  const auto& face=fontFace(size);
  while(*text){
    const char* end=text;
    const char* space=nullptr;
    int width=0;
    while(*end && width+glyph(face,*end).advance<=264){
      if(*end==' ')space=end;
      width+=glyph(face,*end++).advance;
    }
    if(*end && space)end=space;
    char line[96];
    const auto count=std::min<size_t>(end-text,sizeof(line)-1);
    memcpy(line,text,count);line[count]=0;
    skyLabel(202,y,line,color,size);
    y+=step;text=end;
    while(*text==' ')++text;
  }
  return y;
}
void collectionMark(bool arriving){
  const int x=447,y=59;
  screen.fillRoundRect(x-26,y-12,55,28,4,ink);
  int edge=arriving?gold:white;
  screen.drawRect(x-9,y-7,9,11,edge);screen.drawRect(x,y-7,9,11,edge);
  label(x-21,y+6,"Journal",edge,1);
}
void play(const View& v){
  const int light=v.timeMode==4?pondPeriod():v.game.timeSlot;
  if(cachedSite!=v.destination||cachedTime!=light||cachedWeather!=int(v.game.weather)||!background){
    landscape(v.destination,light,v.game.weather);cachedSite=v.destination;cachedTime=light;cachedWeather=int(v.game.weather);
    if(background)memcpy(background,screen.getFramebuffer(),480*320*2);
  }else memcpy(screen.getFramebuffer(),background,480*320*2);
  const auto& g=v.game;
  landscapeMotion(v);
  static creek::WeatherStroke sky[creek::maxWeatherStrokes];
  int count=creek::weatherStrokes(sky,g.weather,v.time,g.destination,g.timeSlot);
  for(int i=0;i<count;++i){
    const auto& stroke=sky[i];uint32_t c=creek::weatherInk[stroke.ink];
    uint16_t rgb=uint16_t(((c>>8)&0xf800)|((c>>5)&0x07e0)|((c>>3)&31));
    screen.drawLine(stroke.x,stroke.y,stroke.endX,stroke.endY,rgb);
  }
  if(v.page==Page::Arrival){
    const auto age=v.time-v.arrivalStart;
    static arrival::Frame frame;
    arrival::draw(frame,v.destination,g.site,age);
    auto fb=screen.getFramebuffer();
    arrival::raster(frame,[&](int x,int y,uint8_t ink){
      int k=scenery::LcdSpans::offset(x,y);
      fb[k]=fb[k+1]=fb[k+320]=fb[k+321]=lcd[ink];
    });
    if(age<arrival::raiseRod){
      skyLabel(10,10,creek::destinations[v.destination].name,white,2);
      skyLabel(10,31,arrival::description(arrival::landing(v.destination,g.site)),white,1);
      skyLabel(386,301,"Tap to skip",white,1);
    }
    if(age<arrival::raiseRod)return;
  }
  if(v.page==Page::Play)top(v);
  const int ax=int(g.aimX*480),ay=int(g.aimY*320);
  if(v.page!=Page::Arrival && (g.phase==Phase::Ready || g.phase==Phase::Flight)){
    screen.drawEllipse(ax,ay,8,3,0xde92);
  }
  int bobX=ax+int(4*std::sin(v.time*.0015f));
  int bobY=ay+int(2*std::sin(v.time*.005f));
  if(g.phase==Phase::Flight){float t=creek::limit(g.age/650.f,0,1);bobX=100+int((ax-100)*t);bobY=106+int((ay-106)*t-178*t*(1-t));}
  if(g.phase==Phase::Fight){
    bobX=112+int((ax-112)*creek::limit(g.line/g.target,0,1)+g.pullOffset());
    float drift=g.holdingBottom()?0.f:g.fightStyle()==creek::FightStyle::Picker?2.f:8.f;
    bobY=240+int((ay-240)*creek::limit(g.line/g.target,0,1)+drift*std::sin(g.age*.006f));
  }
  if(g.phase==Phase::Waiting && g.rig==creek::Technique::Spoon)bobX-=int(30*(g.strokes+g.lureTurns));
  if(g.phase==Phase::Waiting && g.rig==creek::Technique::Jig && g.falling)bobY-=int(28*(1-creek::limit((g.age-g.fallStart)/780.f,0,1)));
  if(g.phase==Phase::Bite)bobY+=12;else if(g.teasing())bobY+=4;
  float tilt=creek::limit(v.degrees,-25,80);float wave=std::sin(v.time*.0024f);
  float angle=(48+tilt*.56f+1.2f*wave)*.01745329f;
  const float reach=162*std::cos(angle),rise=162*std::sin(angle),load=g.rodLoad();
  const float sideways=.20f*g.pullOffset();
  const int rodDrop=v.page==Page::Arrival?int(190*(1-arrival::ease(v.time-v.arrivalStart,arrival::raiseRod,arrival::duration-arrival::raiseRod))):0;
  int tipX=12,tip=248+rodDrop;
  for(int n=0;n<14;n++){
    int x=(n*83+int(v.time/(80+n*4)))%472,y=169+(n*19)%78;
    if(std::sin(v.time*.0015f+n)>.15)screen.drawFastHLine(x,y,3+n%7,screen.getFramebuffer()[x*320+319-(y-2)]);
  }
  if(v.page==Page::Play && eventActive()){
    label(14,40,eventStatus(),white,1);label(14,52,cupGoal(),paper,1);label(14,64,cupStanding(),gold,1);label(14,76,cupBait(),paper,1);
  }
  constexpr int rodColors[]={0x7390,0xb344,0x34f6};
  for(int section=1;g.phase!=Phase::Landed && section<=5;section++){
    float t=section*.2f,flex=load*t*t*t;
    int x=12+int(reach*t+11*flex+sideways*t*t*t),y=248+rodDrop-int(rise*t-41*flex+4*t*(1-t));
    screen.drawLine(tipX,tip,x,y,ink);
    if(section<5)screen.drawLine(tipX+1,tip,x+1,y,rodColors[v.rodFinish]);
    tipX=x;tip=y;
  }
  if(g.phase==Phase::Ready){
    int hangX=tipX+int(3*std::sin(v.time*.003f));
    screen.drawLine(tipX,tip,hangX,tip+24,0x73ee);screen.fillRect(hangX-2,tip+24,4,6,gold);
  }
  if(g.phase==Phase::Snag){bobX=ax;bobY=ay;}
  if(g.phase==Phase::HaulingJunk){
    float t=g.target>0?creek::limit(g.line/g.target,0,1):1;
    bobX=112+int((ax-112)*t);bobY=249+int((ay-249)*t);drawWaterProp(2,bobX,bobY-1);
  }
  if(g.running()){
    screen.drawLine(tipX,tip,bobX,bobY,0x73ee);
    if(g.phase!=Phase::Fight&&g.phase!=Phase::Snag&&g.phase!=Phase::HaulingJunk){if(g.rig==creek::Technique::Float){screen.fillRect(bobX-3,bobY-6,7,5,gold);screen.fillRect(bobX-3,bobY-1,7,3,white);}
    else {bool jig=g.rig==creek::Technique::Jig;screen.fillRect(bobX-2,bobY-3,jig?4:10,jig?9:4,white);screen.fillRect(bobX-2,bobY-3,4,3,gold);}
    screen.drawFastHLine(bobX-11,bobY+4,23,paper);}
  }
  if(v.page!=Page::Play)return;
  const char* head="Raise the rod";const char* sub="Then sweep forward to your playing position.";
  char desc[64];int col=white;
  switch(g.phase){
  case Phase::Ready:if(v.raised)head="Cast forward";if(v.practice){head="Tap to cast";sub="Touch practice uses the lower panel.";}break;
  case Phase::Flight:
    snprintf(desc,sizeof(desc),"Casting: %s / %s",creek::baitNames[g.bait%6],creek::depthNames[g.bait/6]);
    head=desc;break;
  case Phase::Waiting:
    if(g.emptyCast)head="Quiet water - check bait and depth";
    else if(g.rig==creek::Technique::Float)head=g.teasing()?"Nibble - hold steady":"Watch the float";
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
    collectionMark(g.filed && g.age>500);
    float t=creek::limit(g.filed?g.age/800.f:0.f,0,1);
    float ease=t*t*(3-2*t),k=3.7f-3.4f*ease;
    if(t<1){
      int cx=100+int(347*ease),cy=158-int(99*ease+46*4*t*(1-t));
      fish(cx-int(24*k),cy-int(12.5f*k),k,g.fish);
    }
    if(g.filed){skyLabel(12,300,"Adding to journal",white,1);return;}
    const char* rewards[]={"Catch landed","Personal best","New species","New species +1 tackle point"};
    const int colors[]={white,0xb717,0xbebf,0xe63f,0xfed1,0x87ff};
    snprintf(desc,sizeof(desc),"%s  /  %s",creek::ranks[f.tier],rewards[int(g.landingReward())]);
    skyLabel(202,71,desc,colors[f.tier],1);
    int afterName=catchLines(f.name,91,white,3,24);
    const int stats=afterName+15;
    skyLabel(202,stats,"Est. weight",paper,1);
    skyLabel(338,stats,creek::sizeLabel(g.fish,g.length),paper,1);
    if(!g.landedGrams)snprintf(desc,sizeof(desc),"Unweighed");
    else if(g.landedGrams<1000)snprintf(desc,sizeof(desc),"%d g",g.landedGrams);
    else snprintf(desc,sizeof(desc),g.landedGrams<10000?"%.2f kg":"%.1f kg",g.landedGrams/1000.);
    skyLabel(202,stats+16,desc,white,3);
    snprintf(desc,sizeof(desc),"%d cm",g.length);
    skyLabel(338,stats+16,desc,white,3);
    snprintf(desc,sizeof(desc),"Origin / %s",creek::destinations[v.destination].name);
    const int originEnd=catchLines(desc,stats+50,gold,2,18);
    const bool fictional=g.fish>=creek::originalSpecies&&g.fish<creek::originalSpecies+8;
    if(fictional){
      char legend[130];snprintf(legend,sizeof(legend),"Fictional - %s",f.lore);catchLines(legend,originEnd+4,paper,2,17);
    }else catchLines(f.lore[0]?f.lore:"Family illustration / game size estimate",originEnd+4,paper,2,17);
    skyLabel(12,300,"Tap to add to journal",white,1);
    return;}
  case Phase::Snag:
    head=g.contact==1?"Branch snag: stop, then lift":"Rock snag: lower rod and pay out";
    if(v.practice)head=g.contact==1?"Branch snag: wait, then tap to lift":"Rock snag: tap twice to pay out";
    col=gold;tensionLight(.7f);break;
  case Phase::HaulingJunk:head="Debris on the line: reel it ashore";break;
  case Phase::JunkLanded:{
    const char* names[]={"Waterlogged sandal","Tangled line","Dented cup","Torn float"};
    const int id=std::max(0,std::min(3,int(g.junkId)));
    drawWaterProp(3+id,239,135,3);snprintf(desc,sizeof(desc),"Recovered: %s",names[id]);
    head=desc;break;}
  case Phase::Lost:
    head=g.reason==creek::Reason::NoBite?"No bites - Rod workshop: bait + depth":g.reason==creek::Reason::Early?"Hook set too early":g.reason==creek::Reason::Late?"The bite passed":g.reason==creek::Reason::Snapped?"The line snapped":g.reason==creek::Reason::Unworked?"The fish lost interest":"The fish slipped away";
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
 char sky[48];snprintf(sky,sizeof(sky),"Weather: %s >",creek::weatherChoices[v.pendingWeather]);
 screen.drawRoundRect(menuui::x+130,menuui::y+3,173,24,4,0x6bf0);
 menuText(138,11,sky,gold,1);
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
 const auto& journal=v.game.progress.book;const int site=v.bookWater;char buf[110];
 menuHeader("FISH COLLECTION");
 const int caught=journal.waterCount(site,v.destination,BookFilter::Caught),total=stockSize(site);
 const int shown=journal.waterCount(site,v.destination,v.bookFilter);
 snprintf(buf,sizeof(buf),"%s   %d / %d   > Change water",sites[site].name,caught,total);
 menuText(12,38,buf,gold,1);
 const int start=v.bookPage*menuui::bookRows;int match=0,rows=0;
 for(int k=0;k<total && rows<menuui::bookRows;k++){
   const int id=stockId(site,k);const auto& e=journal.entries[id];
   if(!journal.visible(id,v.destination,v.bookFilter))continue;
   if(match++<start)continue;
   int y=56+43*rows++;
   menuText(12,y,catalog[id].name,e.count?white:green);
   if(e.count)snprintf(buf,sizeof(buf),"%s | %lu caught | best %u cm",ranks[catalog[id].tier],(unsigned long)e.count,(unsigned)e.best);
   else if(id>=originalSpecies){
     const auto& species=catalog[id];
     const char* place=species.spot==255?sites[site].name:destinations[species.spot].name;
     char periods[32]="";
     for(int t=0;t<4;++t)if(species.timeMask&(1<<t)){
       const auto used=strlen(periods);snprintf(periods+used,sizeof(periods)-used,"%s%s",used?"/":"",times[t]);
     }
     snprintf(buf,sizeof(buf),"%s | %s | %s",ranks[species.tier],place,periods);
   }else snprintf(buf,sizeof(buf),"%s | %s",ranks[catalog[id].tier],id==prawn?"Dusk ferry piles - lift quickly":id==ray?"Night sandbars - ease off on long runs":times[id%4]);
   menuText(12,y+16,buf,paper,1);
   const int best=preferredChoice(id);
   snprintf(buf,sizeof(buf),"Bait: %s / %s",baitNames[best%6],depthNames[best/6]);
   menuText(12,y+27,buf,gold,1);
 }
 if(!rows)menuText(12,80,"No catches in this water yet.",paper);
 menuText(12,menuui::bookNav+12,"< PREV",gold,1);
 snprintf(buf,sizeof(buf),"%s   %d / %d",v.bookFilter==BookFilter::Nearby?"Here":v.bookFilter==BookFilter::Caught?"Caught":"All species",v.bookPage+1,std::max(1,(shown+menuui::bookRows-1)/menuui::bookRows));
 menuText(130,menuui::bookNav+10,buf);menuText(340,menuui::bookNav+12,"NEXT >",gold,1);
}
void network(){
 menuHeader("WI-FI + CLOCK");menuText(12,38,networkStatus(),white,1);menuText(12,53,updateStatus(),green,1);
 menuText(12,72,setupName(),gold);menuText(12,94,setupCode(),paper,1);menuText(12,111,pondClock());
 menuRow(138,31,"Phone setup","Start");menuRow(169,31,"Online update","Check");
 menuRow(200,31,"Wi-Fi radio",radioEnabled()?"On":"Off");menuRow(231,31,"Shared event",eventActive()?"Joined":"Join");
 menuText(12,263,eventStatus(),green,1);
}
void baitPanel(const View& v){
 menuHeader("HOOK BAIT");const int c=v.game.bait;
 for(int i=0;i<6;i++)menuRow(38+i*27,27,creek::baitNames[i],i==c%6?"Selected":"");
 for(int i=0;i<3;i++)menuText(12+i*(menuui::w/3),220,creek::depthNames[i],c/6==i?gold:white,2);
 const bool locked=v.game.running() || v.game.phase==Phase::Landed;
 menuText(12,251,locked?"Finish or file this catch before changing bait":"Choose the hook bait, then tap a depth",green,1);
}
void journey(const View& v){
 const auto& p=v.game.progress;char buf[80];menuHeader("ROD WORKSHOP");menuText(180,9,"BAIT + DEPTH",gold,1);
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
 if(v.battery.percent>=0){
   snprintf(b,sizeof(b),"%s%d%%",v.battery.charging?"+":"",v.battery.percent);
   label(352,15,b,paper,1);
 }
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
 case Page::Arrival:case Page::Play:play(v);break;case Page::Hub:hub(v);break;case Page::Waters:waters(v);break;
 case Page::Book:book(v);break;case Page::Bait:baitPanel(v);break;case Page::Journey:journey(v);break;case Page::Bench:bench(v);break;
 case Page::TouchCheck:touchCheck(v);break;
 case Page::Network:network();break;case Page::Options:options(v);break;default:calibration(v);break;
 }
 if(v.saveFailed){screen.fillRect(0,302,480,18,ink);label(12,305,"Journal save failed - keep power on and check storage.",red,1);}
 screen.flush();
}

