#include "../WillowCreek/Rumble.cpp"
#include <cstdio>
#include <cassert>
uint32_t testClock=0;
int main(){
 Wire.nack=true;assert(!initRumble());Wire.nack=false;Wire.id=0x60;assert(!initRumble());assert(Wire.log.empty());
 Wire.id=0xe0;assert(initRumble());auto base=Wire.log.size();driveRumble(Pulse::Pull,0,1);assert(Wire.log.size()==base);
 const int effects[3][3]={{63,62,61},{29,28,27},{51,50,49}};
 for(int p=0;p<3;p++)for(int level=1;level<=3;level++){
  assert(driveRumble(static_cast<Pulse>(p+1),level,.3));auto n=Wire.log.size();
  assert(Wire.log[n-3]==std::make_pair(12,0)&&Wire.log[n-2]==std::make_pair(4,effects[p][level-1])&&Wire.log[n-1]==std::make_pair(12,1));
 }
 stopRumble();assert(Wire.log.back()==std::make_pair(12,0));Wire.nack=true;assert(!driveRumble(Pulse::Pull,2,.8f));
 puts("PASS absent and wrong driver IDs, ERM initialization, mute, 9 effect/strength commands, sequencer stop and I2C failure.");
}
