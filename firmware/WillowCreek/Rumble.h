#pragma once
#include "Creek.h"
enum class Pulse {None,Tease,Bite,Pull,Pick,Bottom,Dash,Stop,PickSample,Detent};
struct RumblePlan {
 uint32_t lastPull=0;
 Pulse previous=Pulse::None;
 creek::Phase previousPhase=creek::Phase::Ready;
 Pulse tick(const creek::Game& g,uint32_t now,bool active){
   const auto priorPhase=previousPhase;
   previousPhase=g.phase;
   if(!active){previous=Pulse::None;lastPull=now;return Pulse::None;}
   if((priorPhase==creek::Phase::Snag && g.phase==creek::Phase::Waiting) ||
      (priorPhase==creek::Phase::HaulingJunk && g.phase==creek::Phase::JunkLanded)){
     previous=Pulse::None;lastPull=now;return Pulse::Tease;
   }
   Pulse cue=Pulse::None;
   uint32_t interval=0;
   const auto style=g.fightStyle();
   if(g.teasing())cue=style==creek::FightStyle::Picker?Pulse::Pick:Pulse::Tease;
   if(g.phase==creek::Phase::Bite)cue=Pulse::Bite;
   if(g.phase==creek::Phase::Snag)cue=Pulse::Bottom;
   if(g.phase==creek::Phase::HaulingJunk)cue=Pulse::Pull;
   if(g.phase==creek::Phase::Fight){
     if(style==creek::FightStyle::Picker)cue=g.surge()?Pulse::Pick:Pulse::None;
     else if(g.holdingBottom()){cue=Pulse::Bottom;interval=900;}
     else if(style==creek::FightStyle::Heavy&&g.surge()){cue=Pulse::Dash;interval=600;}
     else if(style==creek::FightStyle::Sprinter&&g.surge()){cue=Pulse::Dash;interval=440;}
     else {cue=Pulse::Pull;interval=(g.surge()?680:1200)-uint32_t(350*g.heat);}
   }
   if(cue!=previous){
     const auto prior=previous;previous=cue;lastPull=now;
     if(cue==Pulse::None && prior!=Pulse::None && !g.running())return Pulse::Stop;
     return cue;
   }
   if(interval && now-lastPull>=interval){lastPull=now;return cue;}
   return Pulse::None;
 }
};
bool initRumble();
bool driveRumble(Pulse pulse,uint8_t level,float tension);
void stopRumble();
