#include "../WillowCreek/Synth.h"
#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>

std::vector<int16_t> render(unsigned spot,int volume,int size,int block,bool preview,bool music=true) {
  CreekSynth synth;synth.begin();
  SoundSettings s;s.site=spot%4;s.arrangement=spot;synth.setSoundscapePreview(preview);s.volume=volume;s.music=music?0:3;
  std::vector<int16_t> data(2*size);
  for(int i=0;i<size;i+=block)synth.render(data.data()+2*i,std::min(block,size-i),s,false,false);
  return data;
}
int main(int argc,char** argv){
 static_assert(BiomeAudio::profile(0)==BiomeAudio::Quiet);
 static_assert(BiomeAudio::profile(1)==BiomeAudio::River);
 static_assert(BiomeAudio::profile(8)==BiomeAudio::Cascade);
 static_assert(BiomeAudio::profile(97)==BiomeAudio::Coast);
 static_assert(BiomeAudio::profile(255)==BiomeAudio::Quiet);
 assert(sizeof(BiomeAudio)<=48);
 CreekSynth synth;synth.begin();SoundSettings s;
 std::array<int16_t,512> a;
 uint64_t golden=14695981039346656037ull;
 for(unsigned i=0;i<4000;i++){
  if(i==2000){s.arrangement=97;s.site=2;}
  if(i==3000)s.music=3;
  synth.render(a.data(),256,s,i%11==0,i%31==0,-1,{},i%43==0?4:0);
  for(auto v:a){golden^=uint16_t(v);golden*=1099511628211ull;}
 }
 // Host PCM fingerprint captured from the unmodified, non-preview mixer.
 assert(golden==0x5db43ecd5219c583ull);
 auto original=render(0,2,768000,128,false);
 auto trial=render(0,2,768000,128,true);
 auto muted=render(0,0,16000,128,true);
 assert(std::all_of(muted.begin(),muted.end(),[](auto x){return x==0;}));
 assert(std::equal(original.begin(),original.begin()+768000,original.begin()+768000));
 // Differences remain when comparing first notes after subtracting their corresponding bed.
 auto bed=render(0,2,768000,128,true,false);
 bool varied=false;
 for(int i=0;i<64000;i++)if(trial[i]-bed[i]!=trial[i+768000]-bed[i+768000])varied=true;
 assert(varied);
 constexpr unsigned spots[]={0,1,8,97};
 std::vector<int16_t> last;
 for(auto spot:spots){
  auto x=render(spot,2,160000,128,true,false);
  assert(x==render(spot,2,160000,256,true,false));
  assert(x!=last);last=x;
  int peak=0;
  for(size_t i=0;i<x.size();i+=2){assert(x[i]==x[i+1]);peak=std::max(peak,std::abs(int(x[i])));}
  assert(peak>50&&peak<=900);
  printf("spot=%u min/max-bounded ambience peak=%d\n",spot,peak);
 }
 BiomeAudio mix;
 std::array<int16_t,256> sine{};
 for (unsigned i=0;i<256;++i) sine[i]=std::lround(std::sin(i*6.2831853/256)*32760);
 std::array<int16_t,64000> prior{};
 for(unsigned i=0;i<64000;++i)prior[i]=mix.sample(97,3,sine.data());
 int maxJump=0,lastSample=prior.back();
 for(unsigned i=0;i<32000;++i){int v=mix.sample(8,3,sine.data());maxJump=std::max(maxJump,std::abs(v-lastSample));lastSample=v;}
 assert(maxJump<800);
 for(unsigned i=0;i<7000;++i)lastSample=mix.sample(8,0,sine.data());
 assert(lastSample==0);
 BiomeAudio full,duck;
 int64_t fullAbs=0,duckAbs=0;
 for(unsigned i=0;i<32000;++i){
  const int loud=full.sample(1,1,sine.data()),quiet=duck.sample(1,1,sine.data(),true);
  if(i>7000){fullAbs+=std::abs(loud);duckAbs+=std::abs(quiet);}
 }
 assert(duckAbs*2<fullAbs&&duckAbs>0);
 if(argc>1){
  FILE* f=std::fopen(argv[1],"wb");assert(f);
  for(unsigned spot:{0u,0u,1u,8u,97u}){
   static int track=0;
   // A/B play the same first ten seconds of the second score loop.
   const unsigned offset=track<2?songEnds[0]:0;
   auto x=render(spot,3,offset+160000,256,track!=0,track<2);++track;
   for(int i=0;i<160000;++i){
    int gain=std::min(8000,std::min(i,159999-i));int16_t y=int(x[(i+offset)*2])*gain/8000;
    std::fwrite(&y,sizeof(y),1,f);
   }
   int16_t gap=0;for(int i=0;i<4000;++i)std::fwrite(&gap,sizeof(gap),1,f);
  }
  std::fclose(f);
 }
 puts("PASS: baseline bit-exact, profiles, PCM bounds, block-invariance, variation, smooth change, mute.");
}
