#include "../WillowCreek/ReelDetents.h"
#include "../WillowCreek/Synth.h"
#include <array>
#include <cassert>
#include <cstdio>

int main(){
  ReelDetents detents;
  for(int sign:{1,-1}){
    int count=0;
    for(int i=0;i<128;i++)count+=detents.measure(sign/128.f);
    assert(count==12*sign && detents.remainder==0);
  }
  for(int i=0;i<1000;i++){
    assert(detents.measure(.0009765625f)==0);
    assert(detents.measure(-.0009765625f)==0);
  }
  assert(detents.feedback(1,Pulse::Bite,100)==0);
  assert(detents.feedback(1,Pulse::None,400)==0);
  assert(detents.feedback(0,Pulse::None,500)==0);
  assert(detents.feedback(-2,Pulse::None,550)==-1);
  assert(detents.feedback(-1,Pulse::None,565)==0);
  assert(detents.feedback(0,Pulse::None,700)==0);
  assert(detents.feedback(1,Pulse::None,730)==1);
  assert(detents.feedback(1,Pulse::Bottom,800)==0);
  assert(detents.feedback(1,Pulse::None,1100)==0);

  SoundSettings sound;sound.volume=sound.cueVolume=0;
  auto strike=[&](unsigned level,int direction){
    CreekSynth source;source.begin();sound.reelVolume=level;
    std::array<int16_t,640> pcm{};
    source.render(pcm.data(),320,sound,false,false,direction);
    assert(std::all_of(pcm.begin()+2*240,pcm.end(),[](int n){return n==0;}));
    return pcm;
  };
  auto mute=strike(0,1),rest=strike(3,0),forward=strike(2,1),reverse=strike(2,-1);
  assert(mute==rest && mute!=forward && forward!=reverse);
  auto low=strike(1,1),high=strike(3,1);
  unsigned long lowPower=0,highPower=0;
  for(size_t i=0;i<low.size();i++){lowPower+=std::abs(low[i]);highPower+=std::abs(high[i]);}
  assert(lowPower>0 && highPower>2*lowPower);
  std::puts("PASS signed 12-tooth traversal, anti-jitter, fish cue priority, bounded feedback, CW/CCW click transients, mute and level.");
}
