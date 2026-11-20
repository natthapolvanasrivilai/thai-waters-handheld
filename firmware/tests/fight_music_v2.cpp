#include "../WillowCreek/Synth.h"
#include <cassert>
#include <cstdio>
#include <vector>

static std::vector<int16_t> clip(CreekSynth& synth,bool surge,unsigned n,bool bite=false){
 SoundSettings s;s.arrangement=8;
 std::vector<int16_t> out(2*n);synth.render(out.data(),n,s,true,bite,0,{},0,false,surge);return out;
}

static std::vector<int16_t> loopPcm(bool surge, unsigned block){
 CreekSynth synth;synth.begin();
 SoundSettings s;s.music=2;s.arrangement=8;
 constexpr unsigned length=locationaudio::fightPickupSamples+4*128*locationaudio::fightTickSamples;
 std::vector<int16_t> out(2*length);
 for(unsigned i=0;i<length;i+=block)
   synth.render(out.data()+2*i,std::min(block,length-i),s,true,false,0,{},0,false,surge);
 return out;
}

static void checkLoopSeams(bool surge){
 constexpr unsigned pickup=locationaudio::fightPickupSamples;
 constexpr unsigned period=128*locationaudio::fightTickSamples;
 static_assert(period==240000,"Eight 4/4 bars at 128 BPM and 16 kHz");
 const auto data=loopPcm(surge,128);
 assert(data==loopPcm(surge,256));
 for(unsigned wrap=1;wrap<=3;++wrap){
   const unsigned boundary=2*(pickup+wrap*period);
   assert(data[boundary-4]==0 && data[boundary-2]==0 &&
          data[boundary]==0 && data[boundary+2]==0);
   // The brief zero-crossing is not a break in the rhythm. Real notes
   // occur on both sides within 2 ms, with no sharp transient at the seam.
   const auto mid=data.begin()+boundary;
   const auto audible=[](int16_t sample){return sample!=0;};
   assert(std::any_of(mid-64,mid,audible) && std::any_of(mid,mid+64,audible));
   for(unsigned i=boundary-32;i<boundary+32;i+=2)
     assert(std::abs(int(data[i+2])-int(data[i]))<=8);
   // Once the surge envelope settles, full periods repeat without inserting
   // the pickup or exit. With no surge, the first period matches as well.
   if(wrap>1 || !surge)
     assert(std::equal(mid-2*period,mid,mid));
 }
}

int main(){
 CreekSynth hold,run;hold.begin();run.begin();
 assert(clip(hold,false,8000)==clip(run,false,8000));
 const auto quiet=clip(hold,false,64000);
 const auto active=clip(run,true,64000);
 assert(quiet!=active);
 double eHold=0,eRun=0;int peak=0;
 for(unsigned i=0;i<quiet.size()/2;++i){
    int a=quiet[2*i],b=active[2*i];eHold+=a*a;eRun+=b*b;peak=std::max(peak,std::abs(b));
 }
 assert(eRun>1.25*eHold && peak<22000);
 // Over four seconds later the second half is not just a replay of the first.
 CreekSynth form;form.begin();
 const unsigned half=64*locationaudio::fightTickSamples;
 assert(clip(form,false,half)!=clip(form,false,half));
 assert(form.musicKind()==locationaudio::MusicKind::Action);
 checkLoopSeams(false);checkLoopSeams(true);
 std::puts("Fight loop: exact 240000-frame periods, smooth seams and 128/256-frame block parity");
 std::printf("Fight pressure increases energy %.2fx; composed second half, peak %d\n",eRun/eHold,peak);
}
