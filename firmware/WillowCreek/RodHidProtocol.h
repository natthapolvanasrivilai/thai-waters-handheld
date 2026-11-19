#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

// Keyboard usages are physical USB HID page 0x07 positions.
namespace rodhid {
struct Stream {
  static constexpr int idle=-1,release=0,cast=0x06,lift=0x0b,heartbeat=0x19;
  static constexpr int wind[4]={0x0d,0x18,0x0c,0x12}, unwind[4]={0x0e,0x11,0x10,0x13};
  int counts=0,pitch=-1,sentPitch=-1,down=0;
  uint8_t edges[4]={};
  unsigned first=0,size=0;
  bool initial=true;
  uint32_t lastSlot=0,lastBeat=0,lastPitch=0;
  void sample(float turns,bool castEdge,bool liftEdge,float angle){
    // 4096 magnetic encoder counts make one turn. Cap the pending history
    // if the host stalls so a reconnect never replays old motion.
    counts=std::max(-24*4096,std::min(24*4096,counts+24*int(std::lround(turns*4096))));
    for (int event : {castEdge?cast:0,liftEdge?lift:0}) {
      if(event && size<4){edges[(first+size)%4]=event;++size;}
    }
    if(std::isfinite(angle)){
      angle=std::max(0.f,std::min(1.f,angle));
      const float bin=angle*8;
      if(pitch<0||std::abs(bin-pitch)>.62f)pitch=int(std::lround(bin));
    }
  }
  int next(uint32_t now) const {
    if (!initial && now-lastSlot<15) return idle;
    if (initial||down) return release;
    if(size)return edges[first];
    if(now-lastBeat>=1000)return heartbeat;
    if(pitch>=0 && ((pitch!=sentPitch && now-lastPitch>=80)||now-lastPitch>=500))return 0x1e + pitch;
    int steps=std::abs(counts)/4096;
    if(!steps)return idle;
    int exponent=steps>=8?3:steps>=4?2:steps>=2?1:0;
    return (counts>0?wind:unwind)[exponent];
  }
  // Advance only after the BLE controller accepts this notification.
  void sent(int key,uint32_t now){
    lastSlot=now;
    if(initial){initial=false;lastBeat=now-1000;lastPitch=now-500;}
    down=key;
    if(key==release)return;
    if(key==cast||key==lift){first=(first+1)%4;--size;return;}
    if(key==heartbeat){lastBeat=now;return;}
    if(key>=0x1e&&key<=0x26){sentPitch=key-0x1e;lastPitch=now;return;}
    for(int i=0;i<4;++i){
      if(key==wind[i])counts-=4096*(1<<i);
      if(key==unwind[i])counts+=4096*(1<<i);
    }
  }
};
}

