#include "../WillowCreek/Synth.h"
#include <cassert>
#include <cstdio>
#include <vector>
static std::vector<int16_t> play(SoundSettings s,bool strike,bool fight,size_t n=6000){
 CreekSynth engine;engine.begin();std::vector<int16_t> pcm(2*n);engine.render(pcm.data(),n,s,fight,strike);return pcm;
}
int main(){
 SoundSettings s;s.volume=0;s.cueVolume=0;
 auto silence=play(s,true,false);assert(std::all_of(silence.begin(),silence.end(),[](int16_t x){return x==0;}));
 s.cueVolume=2;auto bite=play(s,true,false);
 assert(bite!=silence);
 assert(std::all_of(bite.begin()+3200,bite.begin()+4600,[](int16_t x){return x==0;}));
 s.cue=1;assert(play(s,true,false)==silence);
 s.volume=2;auto calm=play(s,false,false);assert(calm!=silence && play(s,false,true)!=calm);
 s.music=1;assert(play(s,false,false)!=calm);
 s.music=3;assert(play(s,false,true)==silence);
 s=SoundSettings{};std::vector<int16_t> previous;
 for(int site=0;site<4;site++){
   s.site=site;auto count=songEnds[site];auto loop=play(s,false,true,count+6000);
   assert(std::equal(loop.begin(),loop.begin()+12000,loop.begin()+2*count));
   for(size_t i=0;i<loop.size();i+=2){assert(loop[i]==loop[i+1]);assert(std::abs(loop[i])<32760);}
   auto current=play(s,false,false,16000);assert(current!=previous);previous=current;
 }
 std::puts("PASS independent music/cue mute, visual-only, separated bite tones, drift and adaptive arrangements, stereo, loop boundary and PCM headroom");
}
