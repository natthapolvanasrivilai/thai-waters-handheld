#pragma once
#include <stdint.h>

namespace scenery {
// Two independent quiet environmental channels, not music or fishing foley.
// Integer filtering keeps the voice small, portable and sample-stable.
class BoatAmbience {
  uint32_t noise=0x0c138f1du,phase=0;
  int engine=0,foam=0,blend=0,rumble=0;
  static int approach(int value,int target){
    const int d=target-value;
    return value+(d<0?-((-d+255)/256):(d+255)/256);
  }
  static int wave(uint32_t p){
    const int half=int((p>>19)&4095);
    const int round=half*(4096-half)>>12;
    return p&0x80000000u?-round:round;
  }
public:
  int sample(uint16_t mix,unsigned volume){
    if(volume>3)volume=3;
    if(!volume){engine=foam=blend=rumble=0;return 0;}
    engine=approach(engine,int(mix&255)*int(volume)*64);
    foam=approach(foam,int(mix>>8)*int(volume)*64);
    if(!engine&&!foam)return 0;
    noise=1664525u*noise+1013904223u;
    const int air=int((noise>>20)&4095)-2048;
    blend+=(air-blend)/5;
    rumble+=(blend-rumble)/16;
    phase+=21474836u+uint32_t(rumble*32); // broad approximately 80 Hz pulse
    const int sputter=(wave(phase)+wave(phase*2)/3+wave(phase*4)/5)/2+rumble;
    return (sputter*engine+(blend-rumble)*foam/2)/32768;
  }
};
}
