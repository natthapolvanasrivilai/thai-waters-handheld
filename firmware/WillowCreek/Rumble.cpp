#include "Rumble.h"
#include <Wire.h>
namespace {
constexpr uint8_t addr=0x5a;
bool online=false;
bool put(uint8_t reg,uint8_t value){Wire.beginTransmission(addr);Wire.write(reg);Wire.write(value);return Wire.endTransmission()==0;}
}
bool initRumble(){
 Wire.beginTransmission(addr);Wire.write((uint8_t)0);
 if(Wire.endTransmission(false)!=0 || Wire.requestFrom(addr,(size_t)1)!=1 || (Wire.read()>>5)!=7)return false;
 if(!put(1,0))return false;
 delay(2);
 // ERM, open loop, internal ROM trigger. Each effect terminates on the chip.
 online=put(0x0c,0)&&put(3,1)&&put(0x1a,0x36)&&put(0x1d,0xa0)&&put(0x17,0x83)&&put(5,0);
 return online;
}
void stopRumble(){if(online)online=put(0x0c,0);}
bool driveRumble(Pulse p,uint8_t level,float tension){
 if(!online||!level||p==Pulse::None)return online;
 const uint8_t tease[]={0,63,62,61}, bite[]={0,29,28,27}, pull[]={0,51,50,49};
 uint8_t id=p==Pulse::Tease?tease[level]:p==Pulse::Bite?bite[level]:pull[level];
 if(p==Pulse::Pull && tension>.65f && level>1)--id;
 online=put(0x0c,0)&&put(4,id)&&put(0x0c,1);return online;
}
