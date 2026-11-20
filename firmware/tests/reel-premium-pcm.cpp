#include "../WillowCreek/Synth.h"
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
using Clip=std::array<int16_t,640>;
Clip click(int band,int volume,bool bite=false,bool reveal=false){
 CreekSynth player;player.begin();SoundSettings s;
 s.music=3;s.volume=0;s.cueVolume=2;s.reelVolume=volume;
 Clip pcm{};
 player.render(pcm.data(),320,s,false,bite,band,reveal?creek::LandingCue{1,creek::LandingReward::Catch}:creek::LandingCue{});
 return pcm;
}
int main(){
 const auto lo=click(1,2),mid=click(2,2),fast=click(3,2),reverse=click(-2,2),zero=click(0,2);
 assert(lo!=mid&&mid!=fast&&lo!=fast); // The prior synth ignored the speed band.
 assert(reverse!=mid&&zero==click(3,0)&&lo!=zero);
 for(const auto* c:{&lo,&mid,&fast,&reverse}){
  size_t last=0;int peak=0;
  for(size_t i=0;i<c->size();i+=2){
   assert((*c)[i]==(*c)[i+1]);
   peak=std::max(peak,std::abs(int((*c)[i])));
   if((*c)[i])last=i/2;
  }
  assert(last>=80&&last<150);
  assert(peak>=1250&&peak<=2200);
  printf("tap peak %d, duration %.2fms\n",peak,(last+1)/16.);
 }
 assert(click(3,3,true)==click(0,3,true));
 assert(click(3,3,false,true)==click(0,3,false,true));
 CreekSynth run;run.begin();SoundSettings s;
 s.music=3;s.volume=0;s.cueVolume=0;s.reelVolume=2;
 Clip pcm{};run.render(pcm.data(),32,s,false,false,3);
 assert(std::any_of(pcm.begin(),pcm.begin()+64,[](int v){return v!=0;}));
 s.reelVolume=0;run.render(pcm.data(),32,s,false,false,0);
 assert(std::all_of(pcm.begin(),pcm.begin()+64,[](int v){return v==0;}));
 s.reelVolume=2;run.render(pcm.data(),32,s,false,false,0);
 assert(std::all_of(pcm.begin(),pcm.begin()+64,[](int v){return v==0;}));
 puts("PASS three distinct quiet speed bands, signed character, bounded/muted tails and bite/reveal priority.");
}
