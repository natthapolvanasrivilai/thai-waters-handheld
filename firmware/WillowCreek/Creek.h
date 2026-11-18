#pragma once
#include "Waters.h"
#include <cmath>
#include <cstdint>
#include <algorithm>

namespace creek {
struct Vec { float x=0, y=0, z=0; };
inline float dot(Vec a, Vec b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
inline float limit(float x,float lo,float hi) { return std::min(hi,std::max(lo,x)); }
inline Vec unit(Vec v) {
  float n=std::sqrt(dot(v,v));
  return n>0.001f ? Vec{v.x/n,v.y/n,v.z/n} : Vec{};
}
struct Calibration {
  Vec rest, raised;
  float span() const {return std::acos(limit(dot(unit(rest),unit(raised)),-1,1))*57.29578f;}
  bool valid() const {
    return std::abs(dot(rest,rest)-1)<.04f && std::abs(dot(raised,raised)-1)<.04f && span()>=20 && span()<=85;
  }
  float tilt(Vec g) const {
    float c=dot(rest,raised);
    Vec axis=unit({raised.x-c*rest.x,raised.y-c*rest.y,raised.z-c*rest.z});
    return std::atan2(dot(g,axis),dot(g,rest))*57.29578f;
  }
};
struct Gesture {
  bool high=false, rise=false, cast=false, hadLow=false;
  uint32_t lastHigh=0;
  void sample(float angle,float span,uint32_t now) {
    rise=cast=false;
    if(angle>=.70f*span){
      rise=!high && hadLow; high=true; lastHigh=now; hadLow=false;
    } else if(angle<.27f*span) {
      cast=high && now-lastHigh<=900; high=false; hadLow=true;
    }
  }
};
struct Wheel {
  int previous=-1;
  uint32_t last=0;
  float read(int raw, bool fieldOK, uint32_t now, bool reversed) {
    if(!fieldOK){previous=-1;return 0;}
    int old=previous;previous=raw;
    uint32_t dt=now-last;last=now;
    if(old<0 || dt==0 || dt>90)return 0;
    int change=(raw-old+6144)%4096-2048;
    if(std::abs(change)>8+static_cast<int>(dt*24.576f))return 0; // 6 turns/s
    return (reversed?-change:change)/4096.f;
  }
};
enum class Phase : uint8_t { Ready, Flight, Waiting, Bite, Fight, Landed, Lost };
enum class Reason : uint8_t { None, Early, Late, Snapped, Escaped };
struct Game {
  Progress progress;
  bool personalBest=false,newEntry=false;int pointsAwarded=0;
  Phase phase=Phase::Ready;
  Reason reason=Reason::None;
  uint32_t age=0, waitMs=3200, seed=1;
  int timeSlot=0, site=0, catches=0, fish=0, length=0;
  float line=0, target=0, heat=0, idle=0;
  uint32_t randomInt(uint32_t n){seed=1664525u*seed+1013904223u;return (seed>>8)%n;}
  bool running() const {return phase!=Phase::Ready && phase!=Phase::Landed && phase!=Phase::Lost;}
  bool teasing() const {return phase==Phase::Waiting && age>=waitMs-1000 && age<waitMs-750;}
  bool surge() const {return phase==Phase::Fight && (age+fish*290)%4000>(fish==ray?1750u:2700u);}
  void enter(Phase p){phase=p;age=0;}
  void lose(Reason why){reason=why;enter(Phase::Lost);}
  void tick(uint32_t ms,bool cast,bool rise,float turns) {
    age+=ms;
    const float dt=ms*.001f;
    switch(phase){
    case Phase::Ready: case Phase::Landed: case Phase::Lost:
      if(cast){
        int total=0;
        for(int i=0;i<stockSize(site);i++)total+=encounterWeight(stockId(site,i),timeSlot);
        int ticket=randomInt(total);
        for(int i=0;i<stockSize(site);i++){
          fish=stockId(site,i);int w=encounterWeight(fish,timeSlot);if(ticket<w)break;ticket-=w;
        }
        const auto& species=catalog[fish];
        length=species.low+randomInt(species.high-species.low+1);
        waitMs=2000+randomInt(3500);target=4.f+std::min(9.f,length*.065f);if(fish==ray)target+=3;line=target;heat=.16f;idle=0;
        reason=Reason::None;enter(Phase::Flight);
      }
      break;
    case Phase::Flight: if(age>=650)enter(Phase::Waiting);break;
    case Phase::Waiting:
      if(age>=waitMs)enter(Phase::Bite);
      else if(rise)lose(Reason::Early);
      break;
    case Phase::Bite:
      if(age>(fish==prawn?820u:fish==ray?1150u:1450u)+150u*progress.rank[0])lose(Reason::Late);
      else if(rise)enter(Phase::Fight);
      break;
    case Phase::Fight:
      line=limit(line-turns*(1.f+.12f*progress.rank[1]),0,target+3);
      heat=limit(heat+std::max(0.f,turns)*(surge()?(fish==ray?.78f:.57f):.20f)*(1.f-.10f*progress.rank[2])-dt*.28f,0,1);
      idle=limit(idle+dt-std::max(0.f,turns)*9.f,0,9);
      if(heat>=.999f)lose(Reason::Snapped);
      else if(idle>=8)lose(Reason::Escaped);
      else if(line<=.001f){int points=progress.points();
        const auto& old=progress.book.entries[fish];newEntry=old.count==0;personalBest=length>old.best;
        progress.book.record(fish,length);pointsAwarded=progress.points()-points;
        ++catches;enter(Phase::Landed);}
      break;
    }
  }
};
} // namespace creek
