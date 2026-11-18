#pragma once
#include "Creek.h"
enum class Pulse {None,Tease,Bite,Pull};
struct RumblePlan {
 uint32_t lastPull=0;bool teased=false,bit=false;
 Pulse tick(const creek::Game& g,uint32_t now,bool active){
   if(!active){lastPull=now;return Pulse::None;}
   if(g.phase!=creek::Phase::Bite)bit=false;
   if(!g.teasing())teased=false;
   if(g.teasing()&&!teased){teased=true;return Pulse::Tease;}
   if(g.phase==creek::Phase::Bite&&!bit){bit=true;return Pulse::Bite;}
   if(g.phase!=creek::Phase::Fight){lastPull=now;return Pulse::None;}
   uint32_t period=(g.surge()?680:1200)-uint32_t(350*g.heat);
   if(now-lastPull>=period){lastPull=now;return Pulse::Pull;}
   return Pulse::None;
 }
};
bool initRumble();
bool driveRumble(Pulse pulse,uint8_t level,float tension);
void stopRumble();
