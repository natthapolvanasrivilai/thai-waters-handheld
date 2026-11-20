#pragma once
#include <stdint.h>

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

class Pawl {
  unsigned age=0,length=0,profile=0;
  uint32_t noise=1,body=0,edge=0,bodyStep=0,edgeStep=0;
  int brushed=0,previousBright=0;
  static constexpr uint32_t step(unsigned hz){return uint32_t((uint64_t(hz)<<32)/16000);}
public:
  void clear(){length=0;age=0;}
  void strike(int band){
    const bool reverse=band<0;
    unsigned b=unsigned(reverse?-band:band);
    profile=b>=3?2:b>=2?1:0;
    constexpr unsigned lows[]={436,505,585},metal[]={1460,1595,1740},frames[]={139,128,118};
    age=0;length=frames[profile];brushed=0;previousBright=0;
    body=0;edge=0x13000000u;
    bodyStep=step(lows[profile]+(reverse?0:32));edgeStep=step(metal[profile]+(reverse?35:0));
  }
  int sample(const int16_t* sine,unsigned level){
    if(!level){clear();return 0;}
    if(age>=length)return 0;
    const unsigned left=length-age,attack=age<2?age:2;
    const unsigned transient=profile==2?24:profile==1?29:33;
    noise=1664525u*noise+1013904223u;
    const int source=int(noise>>24)-128;
    brushed+=(source-brushed)/3;
    const int bright=source-brushed;
    const int impact=(3*bright-previousBright)*4;
    previousBright=bright;
    const int strike=age<transient?impact*int(transient-age)/int(transient):0;
    const int weight=int(left*left*512/(length*length));
    const int bodyTone=int(sine[body>>24])*weight/(512*(profile==0?135:profile==1?145:155));
    const unsigned edgeTail=age<55?55-age:0;
    const int edgeTone=int(sine[edge>>24])*int(edgeTail*edgeTail)/(3025*(profile==0?56:profile==1?58:60));
    body+=bodyStep;edge+=edgeStep;++age;
    // Keep the brief metallic strike ahead of the faint body resonance.
    return (strike+bodyTone+edgeTone)*int(attack)*int(level)*17/40;
  }
};
}
