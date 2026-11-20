#pragma once
#include "ScenicRecipes.h"
#include <stdint.h>

// Original procedural audio: no clips, heap, floating-point work or I/O.
class BiomeAudio {
public:
  enum Bed : uint8_t { Quiet, River, Cascade, Coast };
  static constexpr Bed profile(unsigned spot) {
    if(spot>=sizeof(scenery::recipes)/sizeof(*scenery::recipes))return Quiet;
    using namespace scenery;
    switch(recipes[spot].water) {
      case Gulf: case Island: case Headland: case Estuary: return Coast;
      case Stream: return Cascade; // Stylized fast water, not a mapped waterfall.
      case Bend: case Wide: case Gorge: return River;
      default: return Quiet;
    }
  }
  int sample(unsigned spot, unsigned gain, const int16_t* sine, bool duck=false) {
    // Slew individual bed levels, including across a destination change.
    const auto bed=profile(spot);
    for(unsigned i=0;i<4;++i){
      const int target=i==bed?int(gain*(duck?512:2048)):0;
      level[i]+=(level[i]<target)-(level[i]>target);
    }
    if(!(level[0]|level[1]|level[2]|level[3])){boatLevel=0;return 0;}
    rng=rng*1664525u+1013904223u;
    const int noise=int(rng>>16)-32768;
    mist+=(noise-mist)/8;wind+=(mist-wind)/64;
    const int shimmer=mist-wind;
    ++clock;
    const int wash=(sine[(clock/401u)&255]+32768)/256;
    const int gust=(sine[(clock/619u)&255]+32768)/256;
    const int quiet=wind*(200+gust)/512;
    int river=quiet+shimmer/10;
    const int boatTarget=bed==River && spot<sizeof(scenery::recipes)/sizeof(*scenery::recipes) &&
       (scenery::recipes[spot].feature==scenery::Boat || scenery::recipes[spot].feature==scenery::Ferry) ? 4096 : 0;
    boatLevel+=(boatLevel<boatTarget)-(boatLevel>boatTarget);
    // Decouple the event clock from destination changes and ramp the engine.
    const unsigned beat=clock%480000u;
    const unsigned env=beat<96000u?(beat<48000u?beat:96000u-beat):0;
    river+=(sine[(clock*18790482u)>>24]*int(env/128u)/131072)*boatLevel/4096;
    const unsigned call=clock%173137u;
    if(call>16000u && call<26000u){
      const unsigned chirp=(call-16000u)%5000u;
      if(chirp<1800u){
        const int envelope=int(chirp<900u?chirp:1800u-chirp);
        birdPhase+=180000000u+(chirp*47000u);
        river+=sine[birdPhase>>24]*envelope/115200;
      }
    }
    const int cascade=quiet+shimmer/5;
    const int coast=quiet+shimmer*(40+wash)/768;
    int mix=(quiet*level[0]+river*level[1]+cascade*level[2]+coast*level[3])/28672;
    return mix<-900?-900:mix>900?900:mix;
  }
private:
  uint32_t rng=0xb07a4a89u,clock=0,birdPhase=0;
  int mist=0,wind=0,level[4]{},boatLevel=0;
};
