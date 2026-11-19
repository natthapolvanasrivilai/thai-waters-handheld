#pragma once
#include "Sound.h"
#include "Score.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
class CreekSynth {
  struct Voice {uint32_t phase=0, step=0; int age=0,length=0,amp=0;};
  int16_t sineTable[256]{};
  Voice voice[4]{};
  int playing=-1,arrangement=-1; unsigned cursor=0,clock=0,cueAge=10000;
  uint32_t cuePhase=0;
  unsigned toothAge=144,toothNoise=1,toothPhase=0,toothStep=0;
public:
  void begin(){for(int i=0;i<256;i++)sineTable[i]=std::lround(std::sin(i*6.2831853f/256)*32760);}
  void render(int16_t* buffer,size_t frames,const SoundSettings& s,bool chase,bool trigger,int reelClick=0){
    if(reelClick && !trigger && s.reelVolume){
      toothAge=0;toothPhase=0;
      toothStep=reelClick>0?584115552u:507342336u;
    }
    if(playing!=s.site||arrangement!=s.arrangement){playing=s.site%4;arrangement=s.arrangement;cursor=clock=0;for(auto& v:voice)v=Voice{};} const Note* notes=songs[playing]; if(trigger){cueAge=0;cuePhase=0;}
    for(size_t i=0;i<frames;i++){
      while(cursor<songSizes[playing] && notes[cursor].start==clock){
        const Note& n=notes[cursor++];
        static constexpr unsigned tuning[]={1024,1085,1149,1218,1290,1367,1448};
        unsigned variant=s.arrangement<4?0:1+s.arrangement;
        unsigned key=variant?(variant+n.voice*3+(cursor/(3+variant%5))%3)%7:0;
        unsigned gate=variant?78+(variant*7+n.voice*11)%40:100;
        voice[n.voice]={0,uint32_t(uint64_t(n.step)*tuning[key]/1024),0,int(n.duration*gate/100),n.level};
      }
      int music=0;
      for(int v=0;v<4;v++){
        Voice& o=voice[v];
        if(o.age>=o.length)continue;
        int env=std::min(96,o.age)*std::min(192,o.length-o.age)/192;
        int value=sineTable[o.phase>>24]*o.amp/32768;
        if(s.music!=3 && (v!=1 || s.music!=1) && (v!=3 || (s.music==0 && chase)))music+=value*env/96;
        o.age++;o.phase+=o.step;
      }
      int pcm=music*s.volume/(cueAge<6200?12:4);
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
      if(++clock==songEnds[playing]){clock=0;cursor=0;}
    }
  }
};


