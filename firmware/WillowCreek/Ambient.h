#pragma once
#include "Landscape.h"

namespace scenery {
inline void lcdPalette(const Color* colors,uint16_t* result){
  // The native base is already RGB565. Preserve the identity of its 57 used
  // palette indices for mask tests when two neighboring inks quantize alike.
  for(int i=0;i<57;i++){
    auto c=colors[i];
    uint16_t rgb=uint16_t(((c>>8)&0xf800)|((c>>5)&0x07e0)|((c>>3)&31));
    for(int k=0;k<=i;k++){
      uint16_t candidate=rgb^uint16_t(k);
      bool used=false;
      for(int j=0;j<i;j++)if(result[j]==candidate){used=true;break;}
      if(!used){result[i]=candidate;break;}
    }
  }
}
// The scene is sampled by absolute time. No actors, simulation catch-up or
// animation frames need to be retained when a player leaves a waterway.
inline bool navigates(Feature f){
  return f==Raft||f==Ferry||f==Boat||f==Lamps||f==Sail||f==Basket||f==Paper;
}
inline bool waterInk(int ink){return (ink>=WaterTop&&ink<Far)||ink==Deep||ink==Wake;}
inline int triangle(uint32_t phase,int half){
  int v=int(phase&unsigned(2*half-1));return v<half?v:2*half-1-v;
}
struct Voyage {bool visible; int x,y,dir;};
inline int periodAtUtc(unsigned utcMsOfDay){
  unsigned hour=((utcMsOfDay/3600000)+7)%24;
  return hour<5||hour>=20?3:hour<8?0:hour<17?1:2;
}
inline Voyage voyage(const Layout& s,uint32_t ms,unsigned utcDayPlusOne=0){
  const Feature f=s.recipe.feature;
  if(!navigates(f))return {};
  // One tick is 64 ms. Power-of-two recurrence keeps a 32-bit millis rollover
  // continuous. Paper follows the current. Crewed vessels make return runs.
  const uint32_t t=(ms>>6)+(s.seed&511);
  bool slow=f==Raft||f==Paper||f==Basket||f==Sail;
  unsigned cycle=slow?2048:1024,run=t/cycle,progress=t&(cycle-1);
  unsigned passage=slow?1488:832;
  if(progress>=passage)return {};
  // Make a service decision at departure. At an ICT lighting boundary a
  // vessel already on the water continues into the next band until it exits.
  int servicePeriod=s.period;
  if(utcDayPlusOne){
    unsigned journeyMs=progress*64+(ms&63);
    unsigned leftAt=(utcDayPlusOne-1+86400000-journeyMs)%86400000;
    servicePeriod=periodAtUtc(leftAt);
  }
  bool service=true;
  if(servicePeriod==3){
    if(f==Lamps||s.place==1)service=true;
    else if(f==Raft||f==Ferry||f==Boat)service=(run&3)==0;
    else service=false;
  }else if(f==Lamps&&servicePeriod==1)service=(run&3)==0;
  if(!service)return {};
  int dir=(((s.seed>>11)^(f==Paper?0:run))&1)?-1:1;
  int x=-42+int(324*progress/passage);
  int bob=(f!=Raft&&triangle(t+(s.seed>>18),16)>12)?1:0;
  return {true,dir>0?x:width-1-x,s.horizon+28+int((s.seed>>3)&3)+bob,dir};
}

// Sink.span clips to the framebuffer. Sink.water samples the undisturbed base
// image, keeping moving reflections and ringlets off beaches and structures.
template<class Sink> void wet(Sink& out,int x,int y,int n,int ink){
  int end=minOf(width,x+n);x=maxOf(0,x);
  if(unsigned(y)>=height)return;
  while(x<end){
    while(x<end&&!out.water(x,y))++x;
    int start=x;
    while(x<end&&out.water(x,y))++x;
    if(x>start)out.span(start,y,x-start,ink);
  }
}
template<class Sink> void drawVessel(Sink& out,const Layout& s,Voyage v,uint32_t t){
  if(!v.visible||v.x < -38||v.x>width+38)return;
  Feature f=s.recipe.feature;
  int beam=f==Paper?5:f==Basket?7:f==Raft?13:11;
  auto stroke=[&](int u,int dy,int n,int ink){out.span(v.dir>0?v.x+u:v.x-u-n+1,v.y+dy,n,ink);};
  auto foam=[&](int u,int dy,int n,int ink){wet(out,v.dir>0?v.x+u:v.x-u-n+1,v.y+dy,n,ink);};
  for(int i=0;i<4;i++){
    int trailing=beam+2+int(((t>>2)+i*7)&31);
    int line=trailing<beam+13?5:trailing<beam+24?3:1;
    foam(-trailing,2+i%3,line,Wake);
  }
  foam(-beam+1,3,2*beam-3,Deep);
  if(f==Paper){
    stroke(-5,-2,10,Canvas);stroke(-4,-1,8,Wall);stroke(-3,0,6,Canvas);
    for(int i=0;i<4;i++)stroke(-2+i/2,-2-i,4-i,Canvas);
    return;
  }
  if(f==Raft){
    // Bamboo deck, narrow roof ridge, awning, two open bays, steering pole.
    stroke(-14,0,29,Timber);stroke(-12,1,24,Post);stroke(8,-1,5,Wall);
    for(int i=1;i<=6;i++){stroke(-9,-i,1,Post);stroke(0,-i,1,Timber);stroke(7,-i,1,Post);}
    for(int i=0;i<5;i++)stroke(-12+i,-7-i,22-2*i,i==4?Wall:Roof);
    stroke(-8,-2,4,Timber);stroke(-8,-3,4,Timber);
    stroke(9,-3,2,Post);stroke(9,-4,2,Reed);stroke(9,-5,1,Wall);
    for(int i=0;i<7;i++)stroke(11+i/2,-5+i,1,Post);
  }else{
    stroke(-beam,-1,2*beam+1,Roof);stroke(-beam+1,0,2*beam,Timber);
    stroke(-beam+3,1,2*beam-4,Post);stroke(beam-1,-2,4,Post);stroke(beam+2,-3,2,Post);
    if(f==Ferry||f==Lamps){
      for(int i=2;i<7;i++){stroke(-6,-i,1,Post);stroke(5,-i,1,Post);}
      stroke(-8,-7,16,Canvas);stroke(-6,-8,12,Timber);
      if(f==Lamps||s.period==3)for(int i=-5;i<=4;i+=4)stroke(i,-5,1,Gold);
    }else if(f==Sail){
      for(int i=0;i<15;i++){stroke(0,-2-i,1,Post);stroke(-1-(14-i)/2,-2-i,1+(14-i)/2,Canvas);}
    }else{
      stroke(-4,-5,2,Wall);stroke(-3,-4,2,Post);stroke(-3,-3,3,Post);
      if(f==Basket){stroke(1,-4,5,Timber);stroke(0,-3,7,Gold);}
    }
  }
  if(s.period>=2&&f!=Paper){
    stroke(-5,-4,2,Gold);
    int glint=1+triangle(t>>1,4);foam(-6,5,glint,WaterLight+1);foam(-4,7,1,Wake);
  }
}
template<class Sink> void paintAmbient(Sink& out,const Layout& s,uint32_t ms,unsigned utcDayPlusOne=0){
  uint32_t t=ms>>6;
  Water w=s.recipe.water;
  bool sea=s.place>=96,river=w==Bend||w==Stream||w==Wide||w==Gorge||w==Estuary;
  int drift=(s.seed&1)?1:-1;
  // Gusts rise and fall within a 32.8-second cycle. A local shower lasts
  // roughly 11 seconds per 131-second weather cycle at selected sites.
  int gust=triangle((t>>2)+(s.seed>>8),64);
  unsigned weather=((t+(s.seed>>9))&2047);
  bool rain=(s.seed%5<2)&&weather>=1350&&weather<1520;
  // The front of a high wisp overtakes the static far cloud deck. Restrict
  // its brush to sky pixels, so it passes behind foreground leaves and hills.
  if(sea||w==Lake||rain){
    int phase=int(((t>>3)+(s.seed>>14))&511);
    int x=drift>0?phase-45:width+45-phase;
    int y=5+int((s.seed>>22)%22);
    constexpr int inset[]={4,1,0,6},length[]={8,19,23,11};
    for(int row=0;row<4;row++){
      int start=maxOf(0,x+inset[row]),stop=minOf(width,x+inset[row]+length[row]);
      while(start<stop){
        while(start<stop&&!out.sky(start,y+row))++start;
        int a=start;
        while(start<stop&&out.sky(start,y+row))++start;
        if(start>a)out.span(a,y+row,start-a,Cloud+(row==3?2:0));
      }
    }
  }
  if(!sea&&gust>20){
    // Locate existing reed/leaf edges; only their furthest tip sways.
    for(int i=0;i<8;i++){
      uint32_t a=hash(s.seed+i*89U);
      int x=3+int((a>>8)%52);
      if(a&1)x=width-1-x;
      for(int y=103+int((a>>16)%13);y<155;y++){
        if(out.foliage(x,y)&&!out.foliage(x,y-1)){
          int bend=gust>42?2:1;
          out.span(drift>0?x:x-bend,y-1,1+bend,Reed);
          break;
        }
      }
    }
  }
  for(int i=0;i<(sea?26:19);i++){
    uint32_t a=hash(s.seed+i*101U);
    unsigned phase=t+(a&1023);
    int y=s.horizon+5+int((a>>10)%unsigned(height-s.horizon-8));
    int x=(int((a>>17)&255)+drift*int((phase>>(sea||river?1:2))&255))&255;
    int breath=triangle(phase>>1,16);
    int n=1+breath/(sea?3:5)+(gust>45?2:0);
    if(breath>2)wet(out,x-7,y,n,breath>12?Wake:WaterTop+5);
    if(sea&&breath>9)wet(out,x-8,y+1,2,WaterLight);
  }
  // A narrow band of highlights follows the painted sun or moon path.
  for(int i=0;i<7;i++){
    uint32_t a=hash(s.seed+777U+i);
    int y=s.horizon+8+int((a>>8)%62),splay=(y-s.horizon)/4+3;
    int x=s.sunX-splay+int((a+(t>>2))&31)*2*splay/31;
    wet(out,x,y,1+triangle(t+(a>>16),8)/2,rain?Wake:WaterLight+1);
  }
  if(rain){
    for(int i=0;i<17;i++){
      uint32_t a=hash(s.seed+i*211U);
      unsigned phase=(t+(a&127))&31;
      int x=int((a>>8)%width),y=s.horizon+12+int((a>>18)%62);
      if(phase<16){int u=x+drift*int(phase/4);wet(out,u,y-16+phase,1,Wake);}
      else if(phase<24){int radius=1+int(phase-16)/2;wet(out,x+drift*4-radius,y,2,Wake);wet(out,x+drift*4+radius,y,1,Wake);}
    }
  }else if(s.period!=3){
    // A flock crosses the high sky. The silhouettes change wing pose;
    // bank/sky sampling keeps them behind overhanging branches.
    unsigned phase=(t+(s.seed>>8))&1023;
    for(int i=0;i<(sea?4:3);i++){
      int u=-24+int(phase/2)-6*i,x=drift>0?u:width-1-u;
      int y=10+int((s.seed>>6)%15)+i%3,wing=triangle(t+i*3,8)>3?1:-1;
      for(int k=-2;k<=2;k++)if(unsigned(x+k)<width&&out.sky(x+k,y+(k==0?0:wing)))
        out.span(x+k,y+(k==0?0:wing),1,Wood);
    }
  }
  if(!sea&&!rain&&(s.period==2||s.period==3)&&(w==Marsh||w==Bend||w==Foothill||w==Lake)){
    for(int i=0;i<6;i++){
      uint32_t a=hash(s.seed+i*307U);
      if(triangle((t>>1)+a,32)>23){
        int x=6+int((a>>8)%31)+triangle(t>>2,8)/3;
        out.span((a&1)?x:width-1-x,127+int((a>>16)%20)-triangle(t>>2,8)/3,1,Gold);
      }
    }
  }
  drawVessel(out,s,voyage(s,ms,utcDayPlusOne),t);
}
}
