#pragma once
#include "Rumble.h"

// Count teeth in signed AS5600 counts (4096 counts/turn). The fractional
// remainder changes sign on reversal, so resting jitter cannot build clicks.
struct ReelDetents {
  static constexpr int teeth=12;
  int remainder=0;
  bool quiet=false, ticked=false;
  uint32_t blockedAt=0, quietMs=0, lastTick=0;
  int measure(float turns){
    remainder+=int(std::lround(turns*4096))*teeth;
    int count=remainder/4096;
    remainder-=count*4096;
    return count;
  }
  int feedback(int crossings,Pulse fish,uint32_t now){
    if(fish!=Pulse::None){
      blockedAt=now;quiet=true;
      quietMs=fish==Pulse::PickSample?950:fish==Pulse::Bite?360:fish==Pulse::Bottom?400:fish==Pulse::Dash?220:140;
    }
    if(quiet && now-blockedAt<quietMs)return 0;
    quiet=false;
    // At high speed the motor cannot resolve every tooth. Coalesce crossings
    // in-place; never queue an audible or tactile tail after the reel stops.
    if(!crossings || (ticked && now-lastTick<32))return 0;
    lastTick=now;ticked=true;return crossings>0?1:-1;
  }
};
