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
enum class Reason : uint8_t { None, Early, Late, Snapped, Escaped, Unworked };
enum class Technique : uint8_t { Float, Spoon, Jig };
enum class FightBeat : uint8_t { Recover, Run, Slack };
constexpr const char* techniques[]={"Float drift","Stop-and-go spoon","Vertical jig"};
struct Game {
  Progress progress;
  bool personalBest=false,newEntry=false;int pointsAwarded=0;
  Phase phase=Phase::Ready;
  Reason reason=Reason::None;
  uint32_t age=0, waitMs=3200, seed=1;
  int timeSlot=0, site=0, catches=0, fish=0, length=0;
  int destination=0;
  Technique rig=Technique::Float;
  uint32_t fallStart=0, recoverMs=2450, runMs=1450, slackMs=1100;
  unsigned strokes=0, strokesNeeded=2;
  float lureTurns=0, slack=0;
  bool falling=false,rodHeldHigh=false;
  float line=0, target=0, heat=0, idle=0;
  uint32_t randomInt(uint32_t n){seed=1664525u*seed+1013904223u;return (seed>>8)%n;}
  bool running() const {return phase!=Phase::Ready && phase!=Phase::Landed && phase!=Phase::Lost;}
  bool teasing() const {
    if(phase!=Phase::Waiting)return false;
    if(rig!=Technique::Float)return falling && age-fallStart<240;
    uint32_t lead=age<waitMs?waitMs-age:0;
    return (lead>750 && lead<=1000) || ((fish+destination)%3 && lead>1440 && lead<1640);
  }
  FightBeat beat() const {
    const uint32_t cycle=recoverMs+runMs+slackMs;
    const uint32_t n=age/cycle,t=age%cycle;
    const int shift=n?int((n*383+fish*51+destination*31)%701)-350:0;
    return t<recoverMs+shift?FightBeat::Recover:t<recoverMs+runMs?FightBeat::Run:FightBeat::Slack;
  }
  bool surge() const {return phase==Phase::Fight && beat()==FightBeat::Run;}
  int drawWeight(int id) const {
    bool bottom=id==prawn||id==ray||catalog[id].form==2;
    bool chase=catalog[id].form==1;
    return encounterWeight(id,timeSlot)*(rig==Technique::Jig && bottom?3:rig==Technique::Spoon && chase?3:1);
  }
  void setRig(int id){
    if(id<0||id>2||rig==Technique(id))return;
    rig=Technique(id);if(running())enter(Phase::Ready);
  }
  // Each spoon burst must be followed by a pause. A jig lift must be followed
  // by a full fall; repeated jerks or winding during the fall reset that stroke.
  void present(bool rise,float turns){
    if(age>24000){lose(Reason::Unworked);return;}
    if(rig==Technique::Float){
      if(age>=waitMs)enter(Phase::Bite);
      else if(rise)lose(Reason::Early);
      return;
    }
    if(rig==Technique::Spoon){
      if(std::abs(turns)>.0002f){
        lureTurns=limit(lureTurns+turns,0,1.6f);
        falling=lureTurns>=.58f;fallStart=age;
        if(lureTurns>=1.55f){lureTurns=0;falling=false;}
      }
    }else if(rise){
      falling=true;fallStart=age;
    }else if(falling && rodHeldHigh){
      fallStart=age;
    }else if(std::abs(turns)>.003f){
      falling=false;
    }
    const uint32_t dwell=rig==Technique::Spoon?460u:780u;
    if(falling && age-fallStart>=dwell){
      falling=false;lureTurns=0;
      if(++strokes>=strokesNeeded)enter(Phase::Bite);
    }
  }
  void enter(Phase p){phase=p;age=0;}
  void lose(Reason why){reason=why;enter(Phase::Lost);}
  void tick(uint32_t ms,bool cast,bool rise,float turns) {
    age+=ms;
    const float dt=ms*.001f;
    switch(phase){
    case Phase::Ready: case Phase::Landed: case Phase::Lost:
      if(cast){
        int total=0;
        for(int i=0;i<stockSize(site);i++)total+=drawWeight(stockId(site,i));
        int ticket=randomInt(total);
        for(int i=0;i<stockSize(site);i++){
          fish=stockId(site,i);int w=drawWeight(fish);if(ticket<w)break;ticket-=w;
        }
        const auto& species=catalog[fish];
        length=species.low+randomInt(species.high-species.low+1);
        waitMs=2000+randomInt(3500);target=4.f+std::min(9.f,length*.065f);if(fish==ray)target+=3;line=target;heat=.16f;idle=0;
        strokes=0;strokesNeeded=2+(destination+timeSlot+randomInt(3))%3;
        lureTurns=slack=0;falling=false;
        recoverMs=1600+randomInt(1450);runMs=1050+species.tier*210+randomInt(550);
        if(fish==ray)runMs+=700;
        slackMs=800+randomInt(500);
        reason=Reason::None;enter(Phase::Flight);
      }
      break;
    case Phase::Flight: if(age>=650)enter(Phase::Waiting);break;
    case Phase::Waiting:
      present(rise,turns);
      break;
    case Phase::Bite:
      if(age>(fish==prawn?820u:fish==ray?1150u:1450u)+150u*progress.rank[0])lose(Reason::Late);
      else if(rise)enter(Phase::Fight);
      break;
    case Phase::Fight:{
      const bool run=surge(), loose=beat()==FightBeat::Slack;
      const float forward=std::max(0.f,turns);
      // A fleeing fish takes line. An approaching fish creates slack that must
      // be gathered; winding against a run builds load and makes little headway.
      float gained=turns*(1.f+.12f*progress.rank[1])*(run&&turns>0?.20f:1.f);
      line=limit(line-gained+(run?dt*(.22f+catalog[fish].tier*.04f):0),0,target+3);
      float load=run?.91f+catalog[fish].tier*.065f:.20f;
      heat=limit(heat+forward*load*(1.f-.10f*progress.rank[2])+std::min(0.f,turns)*.66f-dt*(run?.18f:.36f),0,1);
      slack=limit(slack+(loose?dt*.80f:0)-forward*1.4f-std::min(0.f,turns)*.55f,0,2.f);
      idle=limit(idle+dt-std::max(0.f,turns)*9.f,0,9);
      if(heat>=.999f)lose(Reason::Snapped);
      else if(idle>=8 || slack>=1.25f)lose(Reason::Escaped);
      else if(line<=.001f){int points=progress.points();
        const auto& old=progress.book.entries[fish];newEntry=old.count==0;personalBest=length>old.best;
        progress.book.record(fish,length);pointsAwarded=progress.points()-points;
        ++catches;enter(Phase::Landed);}
      break;}
    }
  }
};
} // namespace creek
