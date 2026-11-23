#pragma once
#include <stdint.h>
#include "ReelVoiceBank.h"

namespace reelAudio {
// Stage at most the most recent measured physical tooth before the consumer
// polls. Speed uses sensor interval; the limiter uses the consumer's clock.
// Those are deliberately separate in the browser's reconstructed dial.
class Meter {
  unsigned countsPerSecond=0;
  int signedBand=0,direction=0;
  uint32_t lastClick=0;
  bool hasClock=false;
public:
  void clearInput(){countsPerSecond=0;signedBand=0;direction=0;}
  void observe(float turns,uint32_t sampleMs,int crossings){
    if(!sampleMs){clearInput();return;}
    const int delta=int(turns*4096.f); // Accepted Wheel delta is an exact multiple.
    if(delta){
      const int dir=delta>0?1:-1;
      const unsigned measured=unsigned(delta>0?delta:-delta)*1000/sampleMs;
      unsigned mix=sampleMs>80?80:sampleMs;
      countsPerSecond=direction!=dir||!countsPerSecond?measured:
        (countsPerSecond*(80-mix)+measured*mix)/80;
      direction=dir;
    }else{
      countsPerSecond=countsPerSecond*(sampleMs<80?80-sampleMs:0)/80;
      if(!countsPerSecond)direction=0;
    }
    if(crossings){
      const int band=countsPerSecond<3072?1:countsPerSecond<7782?2:3;
      signedBand=crossings>0?band:-band;
    }
  }
  int take(uint32_t now,bool suppressed){
    const int band=signedBand;signedBand=0; // No backlog, including during suppression.
    if(!band||suppressed||(hasClock&&now-lastClick<24))return 0;
    lastClick=now;hasClock=true;return band;
  }
};

// Existing persisted finish IDs: River reed=0, Copper=1, Kingfisher=2.
constexpr unsigned voiceForFinish(unsigned rodFinish){return rodFinish==1?1:0;}
class Pawl {
  unsigned age=144,voice=0,lane=0,take=0,nextTake=0;
public:
  void clear(){age=144;}
  void strike(int band,unsigned rodFinish){
    voice=voiceForFinish(rodFinish);
    const bool reverse=band<0;
    const unsigned b=unsigned(reverse?-band:band);
    const unsigned speed=b>=3?2:b>=2?1:0;
    // Original event seeds cycle by amplitude band AND direction.
    lane=(speed+3*unsigned((speed%2)!=reverse));
    take=nextTake++%8;age=0;
  }
  int sample(unsigned level){
    if(!level){clear();return 0;}
    if(age>=144)return 0;
    return int(voiceBank[voice][lane][take][age++])*int(level)/2;
  }
};
}
