#pragma once
#include "Sound.h"
#include "LocationAudio.h"
#include "FishingPcm.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
class CreekSynth {
  int16_t sineTable[256]{};
  locationaudio::Score score;
  bool wasHeld=false;
  unsigned cueAge=10000;
  uint32_t cuePhase=0;
  unsigned toothAge=144,toothNoise=1,toothPhase=0,toothStep=0;
  creek::LandingCue landing{};
  unsigned landingNote=0,noteAge=0,noteLength=0;
  uint32_t landingPhase=0,landingStep=0;

  struct FoleyVoice{const int8_t* samples=nullptr;unsigned left=0;};
  FoleyVoice foley[5]{};
  void playFoley(uint8_t edges){
    using namespace fishingpcm;
    if(edges&16){for(auto &v:foley)v={};edges=16;}
    const FoleyVoice clips[]={{Air,sizeof(Air)},{Spool,sizeof(Spool)},{Splash,sizeof(Splash)},{Pull,sizeof(Pull)},{Snap,sizeof(Snap)}};
    for(unsigned i=0;i<5;i++)if(edges&(1u<<i))foley[i]=clips[i];
  }
  int foleySample(const SoundSettings& s){
    int sum=0;
    for(int i=0;i<5;i++){auto &v=foley[i];if(!v.left)continue;
      const int gain=i==1?s.reelVolume:s.cueVolume;
      if(!gain){v.left=0;continue;}
      sum+=*v.samples++*gain*(i==3?13:i==4?33:24);--v.left;
    }
    return sum;
  }
  void nextLandingNote(){
    // The opening identifies rarity. The cadence identifies the journal reward.
    static constexpr uint8_t opening[][6]={{0,2},{1,3},{2,3,5},{3,2,4,5},{0,2,3,5,7},{7,4,6,3,5,8}};
    static constexpr uint8_t openingLength[]={2,2,3,4,5,6};
    static constexpr uint8_t cadence[][3]={{0},{3,5},{4,6,5},{5,6,8}};
    static constexpr uint8_t cadenceLength[]={0,2,3,3};
    static constexpr uint16_t hz[]={523,587,659,784,880,1047,1175,1319,1568};
    const unsigned tier=landing.tier,reward=unsigned(landing.reward);
    const unsigned prefix=openingLength[tier],total=prefix+cadenceLength[reward];
    if(landingNote>=total){landing={};return;}
    const unsigned pitch=landingNote<prefix?opening[tier][landingNote]:cadence[reward][landingNote-prefix];
    ++landingNote;
    noteLength=landingNote==total?3520:landingNote==prefix?2200:landing.tier==5?1320:1520;
    noteAge=0;landingPhase=0;landingStep=uint32_t((uint64_t(hz[pitch])<<32)/16000);
  }
  int landingSample(unsigned level){
    // A quick attack and a decaying second harmonic give a plucked bell sound.
    const int gate=int(noteLength)-160;
    const int decay=std::max(0,gate-int(noteAge));
    const int envelope=std::min(64,int(noteAge))*decay/64;
    const int fundamental=sineTable[landingPhase>>24];
    const int overtone=sineTable[(landingPhase>>23)&255]*decay/gate;
    const int sample=(fundamental/4+overtone/12)*envelope/gate;
    landingPhase+=landingStep;
    if(++noteAge==noteLength)nextLandingNote();
    return sample*int(level)/2;
  }
public:
  void clearFoley(){for(auto &v:foley)v={};}
  void clearCatchAudio(){
    cueAge=10000;cuePhase=0;landing={};
    score.rewardContext(false,255); // active reward releases exclusively on next render
  }
  unsigned locationId() const {return score.locationId();}
  locationaudio::MusicKind musicKind() const {return score.musicKind();}
  void begin(){
    score.reset();wasHeld=false;landing={};clearFoley();
    cueAge=10000;cuePhase=0;toothAge=144;toothNoise=1;toothPhase=toothStep=0;
    for(int i=0;i<256;i++)sineTable[i]=std::lround(std::sin(i*6.2831853f/256)*32760);
  }
  void render(int16_t* buffer,size_t frames,const SoundSettings& s,bool chase,bool trigger,int reelClick=0,creek::LandingCue reveal={},uint8_t fishingSounds=0,bool held=false,bool surge=false,bool lost=false){
    if(fishingSounds)playFoley(fishingSounds);
    const bool cueEnabled=s.cue!=1 && s.cueVolume;
    const bool rewardMusic=held && cueEnabled && s.music!=3 && s.volume;
    score.rewardContext(rewardMusic,reveal.tier);
    if(!cueEnabled || (wasHeld && !held) || rewardMusic)landing={};
    else if(reveal.active()){landing=reveal;landingNote=0;nextLandingNote();}
    wasHeld=held;
    if(reelClick && !trigger && s.reelVolume){
      toothAge=0;toothPhase=0;
      toothStep=reelClick>0?584115552u:507342336u;
    }
    if(trigger){cueAge=0;cuePhase=0;}
    for(size_t i=0;i<frames;i++){
      int pcm=score.sample(s.arrangement,sineTable,s.music,s.volume,chase,cueAge<6200||landing.active(),surge,lost);
      pcm+=foleySample(s);
      if(landing.active())pcm+=landingSample(s.cueVolume);
      if(toothAge<144){
        // A dry pawl impact excites a short metallic ring at 16 kHz.
        toothNoise=1664525u*toothNoise+1013904223u;
        int age=int(toothAge++), decay=144-age;
        int attack=age<28?(int(toothNoise>>24)-128)*(28-age):0;
        int ring=(sineTable[toothPhase>>24]/16)*decay/144;
        toothPhase+=toothStep;
        pcm+=(attack+ring)*decay/144*s.reelVolume/(cueAge<5300?8:2);
      }
      bool first=cueAge<1600,second=cueAge>=2300 && cueAge<5300;
      if((first||second) && s.cue!=1){
        int t=first?int(cueAge):int(cueAge)-2300, len=first?1600:3000;
        int env=std::min(80,t)*std::min(180,len-t)/180;
        pcm+=sineTable[cuePhase>>24]*s.cueVolume/12*env/80;
        cuePhase+=first?265140575u:397275598u; // B5 then F#6
      }
      if(cueAge<10000)cueAge++;
      buffer[i*2]=buffer[i*2+1]=std::max(-32760,std::min(32760,pcm));
    }
  }
};


