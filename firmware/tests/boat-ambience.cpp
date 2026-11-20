#include "Ambient.h"
#include "BoatAmbience.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
using namespace scenery;
int main(){
 Layout place{2740,8,1,66,100,{Wide,Boat}};
 assert(boatSound(place,{})==0);
 assert(boatSound(place,{true,-1,99,1})==0);
 assert(boatSound(place,{true,width,99,1})==0);
 const auto passing=boatSound(place,{true,width/2,99,1});
 assert((passing&255)>0&&(passing>>8)>0);
 place.recipe.feature=Paper;assert(boatSound(place,{true,width/2,99,1})==0);
 place.recipe.feature=Basket;assert(boatSound(place,{true,width/2,99,-1})==0);
 place.recipe.feature=Sail;const auto sail=boatSound(place,{true,width/2,99,1});assert((sail&255)==0&&(sail>>8)>0);
 place.recipe.feature=Raft;const auto raft=boatSound(place,{true,width/2,99,1});assert((raft&255)==0&&(raft>>8)>0);
 BoatAmbience voice,copy;
 int peak=0,count=0;uint64_t energy=0;int minS=32767,maxS=-32767;
 for(int i=0;i<32000;++i){
  const int a=voice.sample(passing,2),b=copy.sample(passing,2);
  assert(a==b);
  if(a)++count;
  const int positive=a<0?-a:a;
  peak=maxOf(peak,positive); minS=minOf(minS,a); maxS=maxOf(maxS,a);
  energy+=a*a;
 }
 assert(peak<=1200&&peak>=135&&count>31000&&minS<-50&&maxS>50);
 assert(voice.sample(passing,0)==0); // Immediate mute after an audible pass.
 for(int i=0;i<512;++i)assert(voice.sample(passing,0)==0);
 std::printf("deterministic same-voyage motor+wake; quiet peak %d; mid-pass mean square %.1f; passive and muted silence\n",peak,energy/32000.);
}
