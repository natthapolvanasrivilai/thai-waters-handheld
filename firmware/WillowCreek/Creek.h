#pragma once
#include "Waters.h"
#include "Bait.h"
#include "Weather.h"
#include "LandingCue.h"
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
  bool high=false, rise=false, cast=false, seenRest=false;
  uint32_t lastHigh=0;
  void sample(float angle,float span,uint32_t now) {
    rise=cast=false;
    if(angle>=.70f*span){
      rise=!high && seenRest; high=true; lastHigh=now;
    } else if(angle<.27f*span) {
      cast=high && seenRest && now-lastHigh<=900; high=false; seenRest=true;
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
enum class Phase : uint8_t { Ready, Flight, Waiting, Bite, Fight, Landed, Lost, Snag, HaulingJunk, JunkLanded };
enum class Reason : uint8_t { None, Early, Late, Snapped, Escaped, Unworked, NoBite };
enum class Technique : uint8_t { Float, Spoon, Jig };
enum class FightBeat : uint8_t { Recover, Run, Slack };
enum class FightStyle : uint8_t { Standard, Picker, Anchor, Sprinter };
constexpr const char* techniques[]={"Float drift","Stop-and-go spoon","Vertical jig"};
struct Game {
  Progress progress;
  bool filed=false;
  int landedGrams=0;
  LandingReward landingReward() const {
    if(emptyCast)return LandingReward::Catch;
    if(filed){
      if(pointsAwarded)return LandingReward::TacklePoint;
      if(newEntry)return LandingReward::Discovery;
      return personalBest?LandingReward::PersonalBest:LandingReward::Catch;
    }
    const auto& entry=progress.book.entries[fish];
    if(entry.count)return length>entry.best?LandingReward::PersonalBest:LandingReward::Catch;
    const int found=progress.book.discovered();
    return Progress::discoveryPoints(found+1)>Progress::discoveryPoints(found)?
      LandingReward::TacklePoint:LandingReward::Discovery;
  }
  bool fileCatch(){
    if(phase!=Phase::Landed || filed || emptyCast)return false;
    const int prior=progress.points();
    const auto& entry=progress.book.entries[fish];
    newEntry=entry.count==0;personalBest=length>entry.best;
    progress.book.record(fish,length);
    pointsAwarded=progress.points()-prior;
    filed=true;age=0;
    return true;
  }
  bool personalBest=false,newEntry=false;int pointsAwarded=0;
  Phase phase=Phase::Ready;
  Reason reason=Reason::None;
  uint32_t age=0, waitMs=3200, seed=1;
  int timeSlot=0, site=0, catches=0, fish=0, length=0;
  int destination=0;
  Technique rig=Technique::Float;
  uint8_t bait=0;
  bool emptyCast=false;
  int baitWeight(int id) const {return baitWeightFor(id,bait,int(rig));}
  bool setBait(int choice){
    if(choice<0 || choice>=baitCount || running() || phase==Phase::Landed)return false;
    bait=choice;return true;
  }
  uint32_t fallStart=0, recoverMs=2450, runMs=1450, slackMs=1100;
  unsigned strokes=0, strokesNeeded=2;
  float lureTurns=0, slack=0;
  bool falling=false,rodHeldHigh=false;
  uint32_t liftedCycle=UINT32_MAX,steadyLiftMs=0;
  float line=0, target=0, heat=0, idle=0;
  float aimX=.50f,aimY=.67f;
  int contact=ClearWater,junkId=-1;
  uint32_t waterTicket=0,easedMs=0;
  uint32_t sessionSeed=0,visitNumber=0;
  bool sessionStarted=false;
  int visitDestination=-1;
  unsigned waterSeason=0;
  void beginSession(uint32_t initialSeed){
    seed=sessionSeed=initialSeed;sessionStarted=true;visitNumber=0;visitDestination=-1;
  }
  void arriveAt(int place){
    if(visitDestination>=0 && place!=visitDestination)++visitNumber;
    visitDestination=destination=place;
  }
  Weather weather=Weather::Clear;
  int weatherMode=0;
  void updateWeather(int month,uint32_t day){
    if(running() || month<1 || month>12)return;
    waterSeason=month<=2 || month>=11?0:month<=5?1:2;
    weather=weatherMode?Weather(weatherMode-1):seasonalWeather(destination,month,day,timeSlot);
  }
  uint32_t nextWaterTicket() const {
    return waterHash(seed^uint32_t(destination+1)*0x9e3779b9u^uint32_t(timeSlot));
  }
  uint32_t waterLayout() const {
    uint32_t origin=sessionStarted?sessionSeed:seed;
    return waterHash(origin^uint32_t(destination+1)*0x9e3779b9u^visitNumber*0x85ebca6bu^waterSeason*977u);
  }
  float givenLine=0;
  uint32_t randomInt(uint32_t n){seed=1664525u*seed+1013904223u;return (seed>>8)%n;}
  bool running() const {return phase!=Phase::Ready && phase!=Phase::Landed && phase!=Phase::Lost && phase!=Phase::JunkLanded;}
  void setAim(float x,float y){
    if(running() || !std::isfinite(x) || !std::isfinite(y))return;
    aimX=limit(x,.08f,.92f);aimY=limit(y,.555f,.875f);
  }
  CastZone castZone(int kind) const {return waterZone(waterLayout(),kind);}
  int featureAt(float x,float y) const {
    for(int kind=Branch;kind<=Debris;++kind)
      if(hasWaterFeature(waterLayout(),destination,site,kind) && castZone(kind).distanceSquared(x,y)<=1.f)return kind;
    return ClearWater;
  }
  float releaseProgress() const {
    if(phase==Phase::Snag)return contact==Branch?limit(easedMs/500.f,0,1):limit(givenLine/.30f,0,1);
    if(phase==Phase::HaulingJunk)return limit(1.f-line/target,0,1);
    return phase==Phase::JunkLanded?1:0;
  }
  void abandonCast(){
    if(phase==Phase::Snag || phase==Phase::HaulingJunk)enter(Phase::Ready);
  }
  void splashdown(){
    int feature=featureAt(aimX,aimY);
    if(feature==Branch || feature==Rock){
      contact=feature;heat=feature==Branch?.37f:.51f;enter(Phase::Snag);return;
    }
    // Only debris present in the submerged layout can be recovered.
    bool inCore=feature==Debris && castZone(Debris).distanceSquared(aimX,aimY)<.30f;
    const unsigned odds=feature==Debris?(inCore?72:38):0;
    if(waterTicket%100<odds){
      contact=Debris;junkId=int((waterTicket>>10)%4);
      target=1.f+.27f*junkId;line=target;heat=.23f;enter(Phase::HaulingJunk);
    }else enter(Phase::Waiting);
  }
  void workSnag(uint32_t ms,bool rise,float turns){
    const float dt=ms*.001f,forward=std::max(0.f,turns);
    heat=limit(heat+forward*.96f-dt*.10f,0,1);
    if(heat>=.999f){lose(Reason::Snapped);return;}
    if(contact==Branch){
      if(forward<=.035f*dt)easedMs=std::min<uint32_t>(500,easedMs+ms);else easedMs=0;
      if(easedMs<500 || !rise)return;
    }else{
      if(!rodHeldHigh && !rise)givenLine=limit(givenLine-turns,0,.30f);
      if(givenLine<.2999f)return;
    }
    contact=ClearWater;heat=.12f;enter(Phase::Waiting);
  }
  FightStyle fightStyle() const {
    if(fish==prawn || (fish>=originalSpecies && catalog[fish].form==3))return FightStyle::Picker;
    if(fish==ray || (fish>=originalSpecies && catalog[fish].form==4))return FightStyle::Anchor;
    // Stable catalog IDs: queenfish, cobia, barracuda, trevally and sailfish.
    if((fish>=47 && fish<=51) || (fish>=originalSpecies && catalog[fish].form==1 && catalog[fish].tier>=2))return FightStyle::Sprinter;
    return FightStyle::Standard;
  }
  bool teasing() const {
    if(phase!=Phase::Waiting || emptyCast)return false;
    if(fightStyle()==FightStyle::Picker){
      if(rig!=Technique::Float){
        const uint32_t fall=age-fallStart;
        return falling && (fall<90 || (fall>=180 && fall<275) || (fall>=350 && fall<440));
      }
      const uint32_t lead=age<waitMs?waitMs-age:0;
      return (lead>1350 && lead<=1490) || (lead>990 && lead<=1130) || (lead>610 && lead<=770);
    }
    if(rig!=Technique::Float)return falling && age-fallStart<240;
    uint32_t lead=age<waitMs?waitMs-age:0;
    return (lead>750 && lead<=1000) || ((fish+destination)%3 && lead>1440 && lead<1640);
  }
  FightBeat beat() const {
    const uint32_t cycle=recoverMs+runMs+slackMs;
    const uint32_t n=age/cycle,t=age%cycle;
    if(fightStyle()==FightStyle::Anchor || fightStyle()==FightStyle::Sprinter){
      if(t<runMs)return liftedCycle==n?FightBeat::Recover:FightBeat::Run;
      return t<runMs+recoverMs?FightBeat::Recover:FightBeat::Slack;
    }
    if(fightStyle()==FightStyle::Picker){
      // Two short tugs during the run window; the gaps can be wound gently.
      if(t>=recoverMs && t<recoverMs+runMs){
        const uint32_t tug=t-recoverMs;
        return (tug<runMs/4 || (tug>=runMs/2 && tug<3*runMs/4))?FightBeat::Run:FightBeat::Recover;
      }
      return t<recoverMs?FightBeat::Recover:FightBeat::Slack;
    }
    const int shift=n?int((n*383+fish*51+destination*31)%701)-350:0;
    return t<recoverMs+shift?FightBeat::Recover:t<recoverMs+runMs?FightBeat::Run:FightBeat::Slack;
  }
  bool surge() const {return phase==Phase::Fight && beat()==FightBeat::Run;}
  bool holdingBottom() const {return fightStyle()==FightStyle::Anchor && surge();}
  float rodLoad() const {
    if(phase==Phase::Snag)return (contact==Branch?.50f:.69f)+.22f*heat;
    if(phase==Phase::HaulingJunk)return .23f+.075f*std::sin(age*.007f);
    const FightStyle style=fightStyle();
    if(phase==Phase::Waiting)return teasing()?(style==FightStyle::Picker?.23f:.16f):0;
    if(phase==Phase::Bite)return style==FightStyle::Picker?.33f:style==FightStyle::Anchor?.68f:.54f;
    if(phase!=Phase::Fight)return 0;
    const FightBeat movement=beat();
    float bend;
    switch(style){
      case FightStyle::Picker: bend=movement==FightBeat::Run?.31f:.10f;break;
      case FightStyle::Anchor: bend=holdingBottom()?.82f:.38f;break;
      case FightStyle::Sprinter: bend=movement==FightBeat::Run?.71f+.13f*std::sin(age*.018f):.28f;break;
      default: bend=movement==FightBeat::Run?.53f:.23f;break;
    }
    if(movement==FightBeat::Slack)bend*=.42f;
    return limit(bend+.16f*heat,0,1);
  }
  float pullOffset() const {
    if(phase!=Phase::Fight)return 0;
    switch(fightStyle()){
      case FightStyle::Picker:return (surge()?5.f:1.6f)*std::sin(age*.021f);
      case FightStyle::Anchor:return holdingBottom()?0:7.f*std::sin(age*.0023f);
      case FightStyle::Sprinter:{
        // Travel laterally during each run, then trace a slower arc on recovery.
        const uint32_t cycle=runMs+recoverMs+slackMs, t=age%cycle;
        const float side=(age/cycle)%2?-1.f:1.f;
        return t<runMs?side*48.f*t/runMs:side*48.f*(1.f-float(t-runMs)/(cycle-runMs));
      }
      default:return (surge()?26.f:11.f)*std::sin(age*.004f);
    }
  }
  int drawWeight(int id) const {
    bool bottom=catalog[id].form>=2;
    bool chase=catalog[id].form==1;
    return baitWeight(id)*encounterWeight(id,timeSlot)*(rig==Technique::Jig && bottom?3:rig==Technique::Spoon && chase?3:1);
  }
  template<class Visit> void visitCandidates(bool expanded,Visit visit) const {
    if(!expanded){
      for(int i=0;i<originalStockSize(site);++i)visit(stockId(site,i));
      return;
    }
    const int groups[]={destination,destinationCount+site};
    for(int group:groups){
      for(int i=bySpot.begin[group];i<bySpot.begin[group+1];++i){
        const int id=bySpot.ids[i];if(waterOf(id)==site)visit(id);
      }
    }
  }
  int drawOrdinary(bool expanded){
    int total=0;
    visitCandidates(expanded,[&](int id){if(catalog[id].tier!=5)total+=drawWeight(id);});
    if(!total)return -1;
    int ticket=randomInt(total),selected=-1;
    visitCandidates(expanded,[&](int id){
      if(selected<0 && catalog[id].tier!=5){
        ticket-=drawWeight(id);if(ticket<0)selected=id;
      }
    });
    return selected;
  }
  int drawFish(){
    // The five authored mythics each have a different location/time window.
    // Their extra gate is independent of the normal site and rig selection.
    const uint32_t roll=waterHash(seed^0x9d2c5680u);
    if((roll & 0x3fff)==0){
      int mythic=-1;
      visitCandidates(true,[&](int id){if(catalog[id].tier==5 && drawWeight(id)>0)mythic=id;});
      if(mythic>=0)return mythic;
    }
    const bool expanded=roll%3==0;
    const int first=drawOrdinary(expanded);
    return first>=0?first:drawOrdinary(!expanded);
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
    const uint32_t dwell=(rig==Technique::Spoon?460u:780u)+int(weather)*40u;
    if(falling && age-fallStart>=dwell){
      falling=false;lureTurns=0;
      if(++strokes>=strokesNeeded)enter(Phase::Bite);
    }
  }
  void enter(Phase p){
    phase=p;age=0;
    if(p==Phase::Landed){
      // The prior journal count survives a pending-catch reload on both platforms.
      const uint32_t sequence=progress.book.entries[fish].count;
      const uint32_t key=sequence ^ (uint32_t(fish+1)<<16) ^ uint32_t(length);
      const int condition=90+waterHash(key)%21;
      landedGrams=int(std::min<int64_t>(INT32_MAX,(int64_t(weightGrams(fish,length))*condition+50)/100));
    }
    if(p==Phase::Ready || p==Phase::Flight){
      contact=ClearWater;junkId=-1;easedMs=0;givenLine=0;
    }
    if(p==Phase::Fight){liftedCycle=UINT32_MAX;steadyLiftMs=0;}
  }
  void lose(Reason why){reason=why;enter(Phase::Lost);}
  void tick(uint32_t ms,bool cast,bool rise,float turns) {
    age+=ms;
    const float dt=ms*.001f;
    switch(phase){
    case Phase::Landed:
      if(filed && age>=800)enter(Phase::Ready);
      break;
    case Phase::Ready: case Phase::Lost: case Phase::JunkLanded:
      if(cast){
        newEntry=false;personalBest=false;pointsAwarded=0;landedGrams=0;
        if(!sessionStarted)beginSession(seed);
        arriveAt(destination);
        waterTicket=nextWaterTicket();
        const int selected=drawFish();
        emptyCast=selected<0;
        if(!emptyCast)fish=selected;
        const auto& species=catalog[fish];
        length=emptyCast?0:species.low+randomInt(species.high-species.low+1);
        if(emptyCast)randomInt(1); // Advance the draw even in completely empty water.
        waitMs=2000+randomInt(3500);
        // In light rain fish feed sooner. Rough surface water slows presentation
        // and increases drag when winding against a run.
        if(weather==Weather::LightRain)waitMs=waitMs*80/100;
        if(weather==Weather::HeavyRain)waitMs+=600;
        if(weather==Weather::Storm)waitMs+=1300;
        target=4.f+std::min(9.f,length*.065f);if(fish==ray)target+=3;line=target;heat=.16f;idle=0;
        strokes=0;strokesNeeded=2+(destination+timeSlot+randomInt(3))%3;
        lureTurns=slack=0;falling=false;
        recoverMs=1600+randomInt(1450);runMs=1050+species.tier*210+randomInt(550);
        slackMs=800+randomInt(500);
        switch(fightStyle()){
          case FightStyle::Picker:recoverMs=1200+recoverMs/4;runMs=660+runMs/6;slackMs=450;break;
          case FightStyle::Anchor:runMs+=700;break;
          case FightStyle::Sprinter:runMs=720+runMs/4;recoverMs+=400;break;
          default:break;
        }
        reason=Reason::None;enter(Phase::Flight);
      }
      break;
    case Phase::Flight: if(age>=650)splashdown();break;
    case Phase::Snag: workSnag(ms,rise,turns);break;
    case Phase::HaulingJunk:
      line=limit(line-turns,0,target);
      if(line<=.001f)enter(Phase::JunkLanded);
      break;
    case Phase::Waiting:
      if(emptyCast){
        if(age>=waitMs)lose(Reason::NoBite);
        break;
      }
      present(rise,turns);
      break;
    case Phase::Bite:
      if(age>(fish==prawn?820u:fish==ray?1150u:1450u)+150u*progress.rank[0])lose(Reason::Late);
      else if(rise)enter(Phase::Fight);
      break;
    case Phase::Fight:{
      const FightStyle style=fightStyle();
      if(holdingBottom() && (rise || rodHeldHigh) && turns<=.10f*dt){
        steadyLiftMs+=ms;
        if(steadyLiftMs>=480)liftedCycle=age/(recoverMs+runMs+slackMs);
      }else steadyLiftMs=0;
      const bool run=surge(), loose=beat()==FightBeat::Slack;
      const float forward=std::max(0.f,turns);
      float purchase=1, payout=0, load=.20f;
      if(run){
        switch(style){
          case FightStyle::Picker:purchase=.55f;payout=.05f;load=1.12f;break;
          case FightStyle::Anchor:purchase=0;payout=0;load=1.38f;break;
          case FightStyle::Sprinter:purchase=.12f;payout=1.05f+catalog[fish].tier*.08f;load=1.12f;break;
          default:purchase=.20f;payout=.22f+catalog[fish].tier*.04f;load=.91f+catalog[fish].tier*.065f;break;
        }
      }
      if(run)load*=1.f+.06f*int(weather);
      const float gained=turns*(1.f+.12f*progress.rank[1])*(turns>0?purchase:1.f);
      line=limit(line-gained+dt*payout,0,target+3);
      heat=limit(heat+forward*load*(1.f-.10f*progress.rank[2])+std::min(0.f,turns)*.66f-dt*(run?.18f:.36f),0,1);
      slack=limit(slack+(loose?dt*.80f:0)-forward*1.4f-std::min(0.f,turns)*.55f,0,2.f);
      idle=limit(idle+dt-std::max(0.f,turns)*9.f,0,9);
      if(heat>=.999f)lose(Reason::Snapped);
      else if(idle>=8 || slack>=1.25f)lose(Reason::Escaped);
      else if(line<=.001f){filed=false;
        ++catches;enter(Phase::Landed);}
      break;}
    }
  }
};
} // namespace creek
