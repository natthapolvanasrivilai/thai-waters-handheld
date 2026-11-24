#include "Scene.h"
#include "ArrivalPixels.h"
#include "LcdGlyphs.h"
#include "WaterArt.h"
#include "RodFeedback.h"
#include "Connected.h"
#include "RodController.h"
#include "AmbientLcd.h"
#include "FishArt.h"
#include "SalvageArt.h"
#include "SpecimenArt.h"
#include "TackleIcons.h"
#include <cstdio>
#include <cstring>
#include <sys/time.h>
static_assert(sizeof(specimen::index)/sizeof(specimen::index[0])==creek::fishCount,"Rebuild the species plate index with the catalog");
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
  uint16_t boat=0;
  scenery::paintAmbient(spans,scenicLayout,ms,utcDayPlusOne,&boat);
  setBoatAmbience(boat,v.page==Page::Play);
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
template<class Pixel> void drawPortrait(int x,int y,float k,const uint16_t* palette,bool silhouette,Pixel pixel){
  for(int row=0;row<50;row++){
    int start=0,prev=0;
    for(int col=0;col<=96;col++){
      int c=col==96?0:pixel(col,row);
      if(c!=prev){if(prev)screen.fillRect(x+int(start*k),y+int(row*k),int(col*k)-int(start*k),int((row+1)*k)-int(row*k),silhouette?0x74af:palette[prev]);start=col;prev=c;}
    }
  }
}
void fish(int x,int y,float k,int kind,bool silhouette=false){
  if(!specimen::has(kind)){
    // The field-note marker remains available for a saved catch whose card is absent.
    const int cx=x+int(24*k),cy=y+int(12*k),r=int(5*k);
    screen.drawRect(cx-r,cy-r,r*2,r*2,0x74af);
    screen.drawLine(cx-r/2,cy+r/2,cx+r/2,cy-r/2,0x74af);
    return;
  }
  const bool field=kind>=60;
  const auto* frame=field?&specimen::frames[specimen::index[kind]]:nullptr;
  const uint16_t* palette=field?frame->ink:fishInk[kind];
  drawPortrait(x,y,k*.5f,palette,silhouette,[&](int col,int row){
    if(field)return specimen::pixel(*frame,col,row);
    int pair=fishArt[kind][row*48+col/2];return col&1?pair&15:pair>>4;
  });
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
void tensionLight(int bobX,int bobY,float tension){
  const int x=std::max(2,std::min(442,bobX-18)),y=std::max(62,std::min(280,bobY-22));
  const int filled=std::min(8,std::max(0,int(std::ceil(tension*8))));
  const int color=tension>=.8f?red:tension>=.55f?gold:green;
  screen.fillRect(x,y,36,8,ink);
  for(int i=0;i<8;i++)screen.fillRect(x+2+i*4,y+2,3,4,i<filled?color:0x428c);
  screen.fillRect(std::max(x+1,std::min(x+32,bobX-1)),y+8,3,2,color);
  if(tension>=.8f){screen.fillRect(x+3,y-11,30,10,ink);label(x+6,y-10,"EASE",gold,1);}
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
  if(v.game.phase==creek::Phase::Landed){
    const char* clock=strstr(t,"needs sync")?"Clock needs sync":t;
    skyLabel(432-textWidth(clock,1),12,clock,white,1,434);batteryIcon(443,10,v.battery);
    return;
  }
  const int rodColor=v.rodFinish==1?0xdd2b:v.rodFinish==2?0x6637:0xb692;
  screen.drawLine(11,42,21,32,ink);screen.drawLine(11,41,21,31,rodColor);screen.drawLine(21,31,29,28,rodColor);
  screen.drawLine(11,41,15,37,gold);screen.fillRect(14,39,3,3,ink);
  if(v.game.rig==creek::Technique::Float){screen.drawFastVLine(42,27,17,white);screen.fillRect(39,31,7,4,red);screen.fillRect(39,35,7,3,white);}
  else if(v.game.rig==creek::Technique::Spoon){screen.drawLine(44,27,38,35,gold);screen.drawLine(45,28,39,36,gold);screen.drawLine(39,36,37,41,white);}
  else{screen.drawLine(41,27,41,34,white);screen.drawLine(39,32,45,39,green);screen.drawLine(45,39,48,36,white);}
  for(int y=0;y<17;y++)for(int x=0;x<28;x++){const uint16_t color=tackleBait[v.game.bait%6][y*28+x];if(color)screen.drawPixel(52+x,26+y,color);}
  screen.drawFastHLine(87,29,14,green);screen.drawFastVLine(94,30,13,ink);screen.fillRect(91,30+v.game.bait/6*5,6,3,white);
  skyLabel(229,12,strstr(t,"needs sync")?"Clock needs sync":t,white,1,361);
  batteryIcon(365,10,v.battery);skyLabel(404,9,"MENU",gold,2);
}
void menuText(int x,int y,const char* text,int color=white,int size=2,int width=0){
  int available=width?width:menuui::w-x-8;
  if(size==2 && textWidth(text,size)>available)size=1;
  label(menuui::x+x,menuui::y+y,text,color,size,menuui::x+x+available);
}
void menuHeader(const char* title,const char* action="BACK",int height=menuui::header){
  auto fb=screen.getFramebuffer();
  // RGB565 channel-aligned arithmetic. Retain one quarter of the actual scene.
  for(int x=0;x<menuui::w;x++)for(int y=0;y<menuui::h;y++){
    int dx=std::min(x,menuui::w-1-x),dy=std::min(y,menuui::h-1-y);
    if(dx<6&&dy<6&&(6-dx)*(6-dx)+(6-dy)*(6-dy)>36)continue;
    auto& pixel=fb[(menuui::x+x)*320+319-(menuui::y+y)];
    pixel=((pixel&0xe79c)>>2)+((ink&0xf7de)>>1)+((ink&0xe79c)>>2);
  }
  screen.drawRoundRect(menuui::x,menuui::y,menuui::w,menuui::h,7,0x6bf0);
  menuText(12,(height-14)/2,title,paper);
  menuText(menuui::w-58,(height-10)/2,action,gold,1);
  screen.drawFastHLine(menuui::x+8,menuui::y+height-1,menuui::w-16,0x526d);
}
void gridButton(int index,int top,int row,const char* name,const char* value){
  int x=(index%2)*menuui::w/2,y=top+(index/2)*row;
  screen.drawRoundRect(menuui::x+x+3,menuui::y+y+2,menuui::w/2-6,row-4,5,0x526d);
  menuText(x+12,y+(row-31)/2,name,white,2,menuui::w/2-22);
  menuText(x+12,y+(row-31)/2+20,value,gold,1,menuui::w/2-22);
}
void options(const View& v){
  const char* music[]={"Adaptive","Drift","Melody","Off"};
  const char* volume[]={"Off","Low","Medium","High"};
  const char* cues[]={"Light + tone","Light","Tone"};
  const char* rows[]={"Music","Music volume","Bite cue","Cue volume","Reel direction","Controls","Rod calibration","Reel click"};
  const char* vals[]={music[v.sound.music],volume[v.sound.volume],cues[v.sound.cue],volume[v.sound.cueVolume],
    v.sound.reverse?"Reversed":"Forward",v.practice?"Touch practice":"Motion + knob","Set two poses",volume[v.sound.reelVolume]};
  menuHeader("SOUND + CONTROLS","BACK",menuui::gridTop);
  for(int i=0;i<8;i++)gridButton(i,menuui::gridTop,menuui::gridRow,rows[i],!v.audio&&i==1?"Codec unavailable":vals[i]);
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
// Paint the two anonymous shapes into the existing water, not on top of the HUD.
void paintFishHint(const creek::FishHint& h){
 if(!h.visible())return;
 const int cx=int(h.x*480),cy=int(h.y*320),scale=h.large?2:1;
 const unsigned shade=unsigned(76*std::min(1.f,5.f*std::min(h.phase,1.f-h.phase)));
 if(!shade)return;
 auto* fb=screen.getFramebuffer();
 for(int y=-3*scale;y<=3*scale;y++)
  for(int x=-11*scale;x<=7*scale;x++){
   const bool body=x*x*9+y*y*49<=441*scale*scale;
   const bool tail=x<=-6*scale&&x>=-11*scale&&std::abs(y)<=(-x-6*scale)*3/5;
   if(!body&&!tail)continue;
   auto& px=fb[(cx+x)*320+319-cy-y];
   const unsigned r=((px>>11)&31)*(256-shade)>>8;
   const unsigned g=((px>>5)&63)*(256-shade/2)>>8;
   const unsigned b=(px&31)*(256-shade/3)>>8;
   px=uint16_t((r<<11)|(g<<5)|b);
  }
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
  if(v.page==Page::Play && (v.practice||(v.motion&&v.field==Field::Good)) && !eventActive())
    paintFishHint(g.fishHint());
  if(v.page==Page::Play)top(v);
  const int ax=int(g.aimX*480),ay=int(g.aimY*320);
  if(v.page!=Page::Arrival && (g.phase==Phase::Ready || g.phase==Phase::Flight)){
    screen.drawEllipse(ax,ay,8,3,0xde92);
  }
  int bobX=ax+int(4*std::sin(v.time*.0015f));
  int bobY=ay+int(2*std::sin(v.time*.005f));
  if(g.phase==Phase::Fight){
    bobX=112+int((ax-112)*creek::limit(g.line/g.target,0,1)+g.pullOffset());
    float drift=g.holdingBottom()?0.f:g.fightStyle()==creek::FightStyle::Picker?2.f:8.f;
    bobY=240+int((ay-240)*creek::limit(g.line/g.target,0,1)+drift*std::sin(g.age*.006f));
  }
  if(g.phase==Phase::Waiting && g.rig==creek::Technique::Spoon)bobX-=int(30*(g.strokes+g.lureTurns));
  if(g.phase==Phase::Waiting && g.rig==creek::Technique::Jig && g.falling)bobY-=int(28*(1-creek::limit((g.age-g.fallStart)/780.f,0,1)));
  if(g.phase==Phase::Bite)bobY+=12;else if(g.teasing())bobY+=4;
  float tilt=creek::limit(v.degrees,-25,80);float wave=std::sin(v.time*.0024f);
  float bend=0;
  if(g.phase==Phase::Flight){
    float a=float(g.age)-creek::castWindupMs;
    bend=a<0?26.f*g.age/creek::castWindupMs:26*std::max(0.f,1-a/145)-13*std::sin(3.14159f*std::min(1.f,a/440));
  }
  float angle=(48+bend+tilt*.56f+1.2f*wave)*.01745329f;
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
  if(g.phase==Phase::Flight){
    float t=creek::limit((float(g.age)-creek::castWindupMs)/(creek::castDurationMs-creek::castWindupMs),0,1);
    bobX=tipX+int((ax-tipX)*t);bobY=tip+15+int((ay-tip-15)*t-178*t*(1-t));
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
  if(g.sprayAge<240 && (g.phase==Phase::Waiting||g.phase==Phase::Fight||g.phase==Phase::Snag||g.phase==Phase::HaulingJunk)){
    float t=g.sprayAge/240.f;for(int i=-2;i<=2;i++)screen.fillRect(bobX+int(i*(2+6*t)),bobY-3-int((11-abs(i)*2)*4*t*(1-t)),2,2,white);
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
    snprintf(desc,sizeof(desc),"Line out %d%%  |  %s",g.target>0?int(g.line/g.target*100.f+.5f):0,v.practice?"Tap for 1/4 turn":"Watch line tension");sub=desc;
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
    if(g.filed){const char* s="Adding to journal";skyLabel((480-textWidth(s,1))/2,300,s,white,1);return;}
    const char* rewards[]={"Catch landed","Personal best","New species","New species +1 tackle point"};
    const int colors[]={white,0xb717,0xbebf,0xe63f,0xfed1,0x87ff};
    const bool trophy=g.trophyCatch();
    if(trophy){
      const int earned=g.landingPoints();
      if(earned)snprintf(desc,sizeof(desc),"Trophy catch / +%d tackle point%s",earned,earned==1?"":"s");
      else snprintf(desc,sizeof(desc),"Trophy catch");
    }else snprintf(desc,sizeof(desc),"%s  /  %s",creek::ranks[f.tier],rewards[int(g.landingReward())]);
    skyLabel(202,71,desc,trophy?gold:colors[f.tier],1);
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
    const char* prompt="Tap to add to journal";
    const float glow=(1.f-std::cos((v.time%2400)*.002617994f))*.5f;
    const int tone=(int(22+9*glow)<<11)|(int(50+13*glow)<<5)|int(23+8*glow);
    skyLabel((480-textWidth(prompt,2))/2,294,prompt,tone,2);
    return;}
  case Phase::Snag:
    head=g.contact==1?"Branch snag: stop, then lift":"Rock snag: lower rod and pay out";
    if(v.practice)head=g.contact==1?"Branch snag: wait, then tap to lift":"Rock snag: tap twice to pay out";
    col=gold;tensionLight(bobX,bobY,std::max(.6f,g.heat));break;
  case Phase::HaulingJunk:head="Debris on the line: reel it ashore";break;
  case Phase::JunkLanded:{
    const int id=g.junkId;
    if(id<0||id>=salvage::count)break;
    drawPortrait(4,108,2,salvage::ink[id],false,[&](int x,int y){
      int pair=salvage::pixels[id][y*48+x/2];return x&1?pair&15:pair>>4;
    });
    skyLabel(202,77,"Recovered",gold,1);
    const int y=catchLines(salvage::items[id].name,100,white,3,24);
    skyLabel(202,y+12,salvage::items[id].group,paper,1);
    catchLines(creek::destinations[v.destination].name,y+34,gold,2,18);
    head=v.practice?"Tap to cast again":"Raise and cast again";break;}
  case Phase::Lost:
    head=g.reason==creek::Reason::NoBite?"No bites - Rod workshop: bait + depth":g.reason==creek::Reason::Early?"Hook set too early":g.reason==creek::Reason::Late?"The bite passed":g.reason==creek::Reason::Snapped?"The line snapped":g.reason==creek::Reason::Unworked?"The fish lost interest":"The fish slipped away";
    sub=v.practice?"Tap to cast again.":"Raise and cast again.";break;
  }
  if(!v.practice && (!v.motion || v.field!=Field::Good)){
    head=!v.motion?"Check the motion sensor":wheelFault(v.field);sub="Paused. Menu offers touch practice.";col=gold;
  }
  char hint[96];snprintf(hint,sizeof(hint),"%s",head);
  if(g.phase==Phase::Fight)snprintf(hint,sizeof(hint),"%s  |  Line out %d%%",head,g.target>0?int(g.line/g.target*100.f+.5f):0);
  if(!v.practice&&(!v.motion||v.field!=Field::Good))snprintf(hint,sizeof(hint),"%s",head);
  int width=12+textWidth(hint,1);
  screen.fillRoundRect(7,296,width,17,3,ink);label(13,301,hint,col,1);
  if(g.phase==Phase::Fight)tensionLight(bobX,bobY,g.heat);
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
 menuHeader("THAI WATERS","RESUME",menuui::gridTop);
 const char* names[]={"Fishing spots","Fish collection","Rod workshop","Bench test","Sound + controls","Touch practice","Connections"};
 const char* values[]={sites[v.game.site].water,"Collection",chapters[v.game.progress.chapter()],"Live readings","Settings",v.practice?"On":"Off","Updates"};
 for(int i=0;i<7;i++)gridButton(i,menuui::gridTop,menuui::gridRow,names[i],values[i]);
}
void waters(const View& v){
 menuHeader("FISHING SPOTS");
 char sky[48];snprintf(sky,sizeof(sky),"Weather: %s >",creek::weatherChoices[v.pendingWeather]);
 screen.drawRoundRect(menuui::x+130,menuui::y+3,173,24,4,0x6bf0);
 menuText(138,11,sky,gold,1);
 for(int i=0;i<4;i++){
   const int id=v.spotPage*4+i;if(id>=destinationCount)break;
   gridButton(i,menuui::gridTop,menuui::waterRow,destinations[id].name,id==v.pendingSite?"Selected":sites[destinations[id].pool].name);
 }
 const char* story=destinations[v.pendingSite].story;
 constexpr int columns=67;
 size_t split=std::min<size_t>(columns,strlen(story));
 if(story[split])while(split && story[split]!=' ')--split;
 char line[columns+1]{};memcpy(line,story,split);menuText(10,148,line,paper,1);
 if(story[split])menuText(10,158,story+split+1,paper,1);
 for(int i=0;i<5;i++){
   int left=i*menuui::w/5;
   if(i==v.pendingTime)screen.drawRect(menuui::x+left+4,menuui::y+menuui::periodY+3,menuui::w/5-8,43,gold);
   menuText(left+10,menuui::periodY+18,i==4?"Live":times[i],i==v.pendingTime?gold:white,1);
 }
 menuText(12,menuui::travelY+19,"< PREV",gold,1);
 screen.fillRoundRect(menuui::x+menuui::w/4,menuui::y+menuui::travelY+3,menuui::w/2,45,5,0x336b);
 menuText(140,menuui::travelY+16,"FISH HERE");menuText(340,menuui::travelY+19,"NEXT >",gold,1);
}
void book(const View& v){
 const auto& journal=v.game.progress.book;const int site=v.bookWater;char buf[110];
 menuHeader("COLLECTION");
 const int caught=journal.waterCount(site,v.destination,BookFilter::Caught),total=stockSize(site);
 const int shown=journal.waterCount(site,v.destination,v.bookFilter);
 snprintf(buf,sizeof(buf),"%s  %d/%d >",site==siteCount?"Thailand":sites[site].name,caught,total);
 menuText(148,20,buf,gold,1,151);
 int drawn=0;
 for(int tile=0;tile<4;tile++){
   const int id=bookTile(v,tile);if(id<0)break;
   const auto& e=journal.entries[id];
   const int x=(tile%2)*menuui::w/2,y=menuui::gridTop+(tile/2)*86;
   screen.drawRoundRect(menuui::x+x+3,menuui::y+y+2,menuui::w/2-6,82,5,0x526d);
   fish(menuui::x+x+10,menuui::y+y+8,1.15f,id,!e.count);
   menuText(x+74,y+15,ranks[catalog[id].tier],e.count?gold:green,1,110);
   menuText(x+10,y+43,e.count?catalog[id].name:"Undiscovered",e.count?white:paper,2,menuui::w/2-20);
   if(e.count)snprintf(buf,sizeof(buf),"%lu caught | best %u cm",(unsigned long)e.count,e.best);
   else snprintf(buf,sizeof(buf),"Tap for habitat and bait");
   menuText(x+10,y+66,buf,green,1,menuui::w/2-20);++drawn;
 }
 if(!drawn)menuText(12,86,"No catches in this water yet.",paper);
 menuText(10,menuui::bookNav+19,"< PREV",gold,1,78);
 snprintf(buf,sizeof(buf),"%s %d/%d",v.bookFilter==BookFilter::Nearby?"Here":v.bookFilter==BookFilter::Caught?"Caught":"All",v.bookPage+1,std::max(1,(shown+menuui::bookRows-1)/menuui::bookRows));
 menuText(103,menuui::bookNav+19,buf,paper,1,85);
 menuText(203,menuui::bookNav+19,"CATCH LOG",gold,1,86);menuText(328,menuui::bookNav+19,"NEXT >",gold,1);
}
void bookDetail(const View& v){
 const int id=v.bookSpecies;if(id<0||id>=fishCount)return;
 const auto& item=catalog[id];const auto& entry=v.game.progress.book.entries[id];char line[108];
 menuHeader("FIELD GUIDE");
 menuText(14,61,entry.count?item.name:"Undiscovered species",white);
 fish(menuui::x+15,menuui::y+91,2.15f,id,!entry.count);
 menuText(140,98,ranks[item.tier],gold);
 if(entry.count)snprintf(line,sizeof(line),"%lu caught | best %u cm",(unsigned long)entry.count,entry.best);
 else snprintf(line,sizeof(line),"Land this species to reveal it.");
 menuText(140,122,line,paper,1);
 if(!specimen::has(id)&&specimen::index[id]>=0)menuText(140,140,"Insert matching art SD and restart.",gold,1);
 const char* place=item.spot==255?sites[waterOf(id)].name:destinations[item.spot].name;
 snprintf(line,sizeof(line),"Water  %s",place);menuText(14,163,line,paper,2);
 char periods[35]{};
 for(int t=0;t<4;t++)if(encounterWeight(id,t)>0){const auto at=strlen(periods);snprintf(periods+at,sizeof(periods)-at,"%s%s",at?" / ":"",times[t]);}
 menuText(14,191,periods,green,2);
 const int best=preferredChoice(id);snprintf(line,sizeof(line),"Bait  %s / %s",baitNames[best%6],depthNames[best/6]);menuText(14,219,line,gold,2);
}
void catchHistory(const View& v){
 menuHeader("CATCH LOG");
 if(v.historyError){menuText(14,85,"Could not read the stored catch.",gold);return;}
 if(!v.historyCount){menuText(14,85,"Your next filed catch starts the log.",paper);return;}
 const auto& r=v.history;char line[120];
 snprintf(line,sizeof(line),"#%lu / %lu",(unsigned long)r.sequence,(unsigned long)v.historyCount);
 menuText(14,56,line,gold,1);menuText(14,75,catalog[r.species].name,white,2);
 snprintf(line,sizeof(line),"%u cm %s  |  %lu g",r.cm,archivedMeasures[r.measurement],(unsigned long)r.grams);
 menuText(14,103,line,paper);
 if(r.flags&TimeKnown){
   time_t local=time_t(r.utc)+7*3600;tm t{};gmtime_r(&local,&t);
   snprintf(line,sizeof(line),"%04d-%02d-%02d   %02d:%02d ICT",1900+t.tm_year,1+t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min);
 }else snprintf(line,sizeof(line),"Time unknown (no verified clock)");
 menuText(14,133,line,gold,2);
 menuText(14,160,r.spot<destinationCount?destinations[r.spot].name:"Location unrecorded",paper,2);
 if(r.period<4 && r.weather<4 && r.bait<18)snprintf(line,sizeof(line),"%s / %s / %s / %s",times[r.period],weatherNames[r.weather],baitNames[r.bait%6],depthNames[r.bait/6]);
 else snprintf(line,sizeof(line),"Legacy catch conditions unrecorded");
 menuText(14,187,line,green,1);
 screen.drawFastHLine(menuui::x+8,menuui::y+menuui::bookNav,menuui::w-16,0x526d);
 menuText(15,menuui::bookNav+18,"< OLDER",r.sequence>1?gold:green,1);
 menuText(292,menuui::bookNav+18,"NEWER >",r.sequence<v.historyCount?gold:green,1);
}

void network(){
 menuHeader("CONNECTIONS","BACK",menuui::gridTop);menuText(12,50,networkStatus(),white,1);menuText(12,64,updateStatus(),green,1);
 menuText(12,78,setupName(),gold,1);menuText(12,92,setupCode(),paper,1);
 const char* names[]={"Phone setup","Online update","Wi-Fi radio","Shared event","Phone controller"};
 const char* values[]={"Wi-Fi","Check",radioEnabled()?"On":"Off",eventActive()?"Joined":"Join","Bluetooth"};
 for(int i=0;i<5;i++)gridButton(i,menuui::networkTop,menuui::networkRow,names[i],values[i]);
 menuText(12,263,eventStatus(),green,1);
}
void phoneController(const View& v){
 menuHeader("PHONE CONTROLLER","BACK",menuui::gridTop);
 menuText(12,51,rodControllerStatus(),green,1);
 menuText(12,64,"iPhone Settings > Bluetooth > Thai Waters Rod",paper,1);
 char line[60];snprintf(line,sizeof(line),"Pairing code: %06u",rodPairCode());
 menuText(12,89,line,gold);
 menuText(12,120,"Open the fishing game in Safari, then enable",paper,1);
 menuText(12,136,"its handheld controller before starting input.",paper,1);
 menuText(12,159,v.calibrated?"Rod calibration ready":"Set rod calibration in Sound + controls",green,1);
 gridButton(0,menuui::controllerTop,menuui::controllerRow,"Send controls",rodControllerStreaming()?"Pause":rodControllerReady()?"Start":"Pair first");
 gridButton(1,menuui::controllerTop,menuui::controllerRow,"Disconnect","Radio off");
}
void baitPanel(const View& v){
 menuHeader("HOOK BAIT");const int c=v.game.bait;
 for(int i=0;i<6;i++)gridButton(i,menuui::gridTop,menuui::baitRow,creek::baitNames[i],i==c%6?"Selected":"");
 const bool locked=v.game.running() || v.game.phase==Phase::Landed;
 menuText(12,205,locked?"Finish or file this catch before changing bait":"Set the fishing depth",green,1);
 for(int i=0;i<3;i++){
   const int x=i*menuui::w/3;
   screen.drawRoundRect(menuui::x+x+4,menuui::y+menuui::depthY+3,menuui::w/3-8,45,5,c/6==i?gold:0x526d);
   menuText(x+12,menuui::depthY+18,creek::depthNames[i],c/6==i?gold:white,2,menuui::w/3-20);
 }
}
void journey(const View& v){
 const auto& p=v.game.progress;char buf[80];menuHeader("ROD WORKSHOP");menuText(180,19,"BAIT + DEPTH",gold,1);
 snprintf(buf,sizeof(buf),"%s  |  %d points",chapters[p.chapter()],p.points());menuText(12,52,buf,gold,1);
 menuText(12,67,story[p.chapter()],green,1);
 gridButton(0,menuui::workshopTop,menuui::workshopRow,"Technique",techniques[int(v.game.rig)]);
 gridButton(1,menuui::workshopTop,menuui::workshopRow,"Rod finish",finishes[v.rodFinish]);
 const char* units[]={"+150 ms","+12% retrieval","-10% tension"};
 for(int i=0;i<3;i++){
   snprintf(buf,sizeof(buf),"%d/3 | %s | cost %d",p.rank[i],units[i],p.rank[i]+1);
   gridButton(i+2,menuui::workshopTop,menuui::workshopRow,paths[i],p.rank[i]==3?"Maximum rank":buf);
 }
 gridButton(5,menuui::workshopTop,menuui::workshopRow,"Refund points",v.refundConfirm?"Tap to confirm":"Retrain");
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
 char cue[15],rumble[15];
 snprintf(cue,sizeof(cue),"Cue level %d/3",v.sound.cueVolume);snprintf(rumble,sizeof(rumble),"Rumble %d/3",v.rumble);
 const char* names[]={v.sound.reverse?"Reel reversed":"Reel forward",cue,"Play bite",rumble,"Tease","Bite","Pull",v.driver?"DRV2605L ready":"Driver absent","Prawn pick","Bottom hold","Fast run","Touch grid"};
 for(int i=0;i<12;i++){
   const int x=i%4*120,y=menuui::benchTop+i/4*menuui::benchRow;
   if(i!=7)screen.drawRoundRect(x+2,y+2,116,48,4,0x526d);
   label(x+8,y+17,names[i],i==7?green:white,2,x+117);
 }

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
 screen.drawRect(52,270,101,49,paper);label(68,294,"BACK",paper,1);
}
}
void paint(const View& v){
 if(!screenOK)return;
 if(v.page!=Page::Play&&!menuui::overlay(v.page)&&v.page!=Page::Arrival)setBoatAmbience(0,false);
 if(menuui::overlay(v.page))play(v);
 switch(v.page){
 case Page::Arrival:case Page::Play:play(v);break;case Page::Hub:hub(v);break;case Page::Waters:waters(v);break;
 case Page::Book:book(v);break;case Page::BookDetail:bookDetail(v);break;case Page::CatchHistory:catchHistory(v);break;case Page::Bait:baitPanel(v);break;case Page::Journey:journey(v);break;case Page::Bench:bench(v);break;
 case Page::TouchCheck:touchCheck(v);break;
 case Page::Controller:phoneController(v);break;case Page::Network:network();break;case Page::Options:options(v);break;default:calibration(v);break;
 }
 if(v.saveFailed){screen.fillRect(0,302,480,18,ink);label(12,305,"Journal save failed - keep power on and check storage.",red,1);}
 screen.flush();
}



