#include "../WillowCreek/Synth.h"
#include "../WillowCreek/Creek.h"
#include <cassert>
#include <cstdio>
#include <vector>
#include <set>
using namespace creek;
static std::vector<int16_t> landingPcm(SoundSettings s,LandingCue cue){
 CreekSynth engine;engine.begin();
 std::vector<int16_t> pcm(2*19200);
 for(size_t i=0;i<pcm.size()/2;i+=128){
   engine.render(pcm.data()+2*i,128,s,false,false,0,i==0?cue:LandingCue{});
 }
 return pcm;
}
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
 s=SoundSettings{};s.volume=0;
 std::set<std::vector<int16_t>> variants;
 for(uint8_t tier=0;tier<6;++tier)for(unsigned reward=0;reward<4;++reward){
   auto pcm=landingPcm(s,{tier,LandingReward(reward)});
   assert(*std::max_element(pcm.begin(),pcm.end())>4000);
   assert(std::all_of(pcm.end()-6400,pcm.end(),[](int16_t x){return x==0;}));
   for(size_t i=0;i<pcm.size();i+=2)assert(pcm[i]==pcm[i+1] && std::abs(pcm[i])<32760);
   assert(variants.insert(pcm).second);
 }
 LandingCue prize{4,LandingReward::TacklePoint};
 const auto noCue=landingPcm(s,{});
 s.cue=1;assert(landingPcm(s,prize)==noCue);
 s.cue=0;s.cueVolume=0;assert(landingPcm(s,prize)==noCue);
 Game fish;fish.fish=3;fish.length=30;
 for(int found=0;found<6;++found){
   fish.progress={};fish.filed=false;fish.phase=Phase::Landed;
   for(int j=0;j<found;++j)fish.progress.book.record(10+j,24);
   auto reward=fish.landingReward();
   assert(reward==(found%3==0?LandingReward::TacklePoint:LandingReward::Discovery));
   assert(fish.progress.book.entries[3].count==0);
   assert(fish.fileCatch() && fish.landingReward()==reward);
 }
 fish.filed=false;fish.length=31;assert(fish.landingReward()==LandingReward::PersonalBest);
 assert(fish.fileCatch() && fish.landingReward()==LandingReward::PersonalBest);
 fish.filed=false;assert(fish.landingReward()==LandingReward::Catch);
 assert(fish.fileCatch() && fish.landingReward()==LandingReward::Catch);
 std::puts("PASS all 24 rarity/reward sounds differ, finish within one second, respect effects mute and light-only, and predict the actual journal reward before filing.");
}
