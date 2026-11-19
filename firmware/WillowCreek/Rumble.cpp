#include "Rumble.h"
#include <Wire.h>
namespace {
constexpr uint8_t addr=0x5a;
// DRV2605L Eq. 6, 21.59 mV/count in open-loop ERM mode.
// 138 counts sets 2.979 V average full-scale for the 3 V ROB-08449.
constexpr uint8_t reelMotorClamp=138;
bool online=false;
bool put(uint8_t reg,uint8_t value){Wire.beginTransmission(addr);Wire.write(reg);Wire.write(value);return Wire.endTransmission()==0;}
}
bool initRumble(){
 Wire.beginTransmission(addr);Wire.write((uint8_t)0);
 if(Wire.endTransmission(false)!=0 || Wire.requestFrom(addr,(size_t)1)!=1 || (Wire.read()>>5)!=7)return false;
 if(!put(1,0))return false;
 delay(2);
 // ERM, open loop, internal ROM trigger. Each effect terminates on the chip.
 online=put(0x0c,0)&&put(3,1)&&put(0x1a,0x36)&&put(0x1d,0xa0)&&put(0x17,reelMotorClamp)&&put(5,0);
 return online;
}
void stopRumble(){if(online)online=put(0x0c,0);}
bool driveRumble(Pulse p,uint8_t level,float tension){
 if(p==Pulse::Stop){stopRumble();return online;}
 if(!online || !level || level>3 || p==Pulse::None)return online;
 if(p==Pulse::Detent){
   constexpr uint8_t tooth[]={9,8,7}; // Single soft bump, separate from the animal motifs.
   online=put(0x0c,0)&&put(4,tooth[level-1])&&put(5,0)&&put(0x0c,1);
   return online;
 }
 // DRV2605L ROM, library 1. All motifs are finite and use the internal trigger.
 static constexpr uint8_t effects[][3]={
   {63,62,61}, {29,28,27}, {51,50,49},
   {6,5,4}, {51,50,49}, {36,35,34}
 };
 const uint8_t index=uint8_t(p==Pulse::PickSample?Pulse::Pick:p)-1;
 if(index>=sizeof(effects)/sizeof(effects[0]))return online;
 uint8_t id=effects[index][level-1];
 if(p==Pulse::PickSample){
   // Three picks spaced like the pre-strike float. A sequencer wait uses 10 ms units.
   constexpr uint8_t gap=0x80|34;
   online=put(0x0c,0)&&put(4,id)&&put(5,gap)&&put(6,id)&&put(7,gap)&&put(8,id)&&put(9,0)&&put(0x0c,1);
   return online;
 }
 if(p==Pulse::Pull && tension>.65f && level>1)--id;
 uint8_t tail=0;
 if(p==Pulse::Bottom)tail=id;                  // Two joined buzzes make a broad load.
 if(p==Pulse::Dash)tail=uint8_t(27-level);    // Double sharp tick followed by one tick.
 online=put(0x0c,0)&&put(4,id)&&put(5,tail)&&(!tail||put(6,0))&&put(0x0c,1);
 return online;
}
