#include "../WillowCreek/Creek.h"
#include "../WillowCreek/ReelDetents.h"
#include "../WillowCreek/ReelAudio.h"
#include <cassert>
#include <cstdio>
static void verifyBand(int counts,int interval,int band){
 for(const int sign:{-1,1}){
  creek::Wheel sensor;ReelDetents teeth;reelAudio::Meter meter;uint32_t dt=99,t=2;
  assert(sensor.read(0,true,t,false,&dt)==0&&dt==0);
  float sum=0;int signedTeeth=0,clicks=0;
  const int packets=4096/counts;
  for(int i=1;i<=packets;++i){
   t+=interval;
   const int raw=(4096+sign*counts*i)&4095;
   const float turns=sensor.read(raw,true,t,false,&dt);
   assert(turns==sign*counts/4096.f&&dt==unsigned(interval));
   const int c=teeth.measure(turns);
   sum+=turns;signedTeeth+=c;
   meter.observe(turns,dt,c);
   if(const int audio=meter.take(20000+t,false)){assert(audio==sign*band);++clicks;}
  }
  assert(sum==sign&&signedTeeth==sign*12&&teeth.remainder==0&&clicks>0);
  assert(meter.take(t+1000,false)==0);
 }
}
int main(){
 verifyBand(32,12,1);verifyBand(64,12,2);verifyBand(128,12,3);
 reelAudio::Meter r;
 r.observe(.125f,24,1);assert(r.take(0xfffffff0u,false)==3);
 r.observe(.125f,14,-1);assert(r.take(3,false)==0);
 assert(r.take(100,false)==0); // Never play a rejected crossing later.
 r.observe(.125f,12,1);assert(r.take(100,false)==3);
 r.observe(.125f,12,1);assert(r.take(124,true)==0);
 assert(r.take(148,false)==0);
 r.observe(.125f,12,-1);
 r.observe(0,0,0);assert(r.take(172,false)==0);
 creek::Wheel s;uint32_t dt=100;
 assert(!s.read(1024,true,1,false,&dt)&&!dt);
 assert(!s.read(2033,true,3,false,&dt)&&!dt); // invalid spike
 assert(!s.read(2040,true,102,false,&dt)&&!dt); // dropout
 assert(!s.read(2040,false,103,false,&dt)&&!dt);
 assert(!s.read(2070,true,104,false,&dt)&&!dt); // redetect anchors first sample
 assert(s.read(2086,true,108,true,&dt)==-16/4096.f&&dt==4);
 std::puts("PASS exact signed 12 teeth/rev for all bands; valid wheel intervals, caps, no backlog, dropout, reversal, suppression and rollover.");
}
