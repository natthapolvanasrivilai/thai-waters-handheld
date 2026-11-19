#include "../WillowCreek/Creek.h"
#include "../WillowCreek/Synth.h"
#include <cassert>
#include <cstdio>
#include <vector>
#include <set>
using namespace creek;
int main(int argc,char** argv){
 Game g;g.beginSession(42);g.setAim(.5f,.6f);
 g.tick(1,true,false,0);assert(g.phase==Phase::Flight&&g.soundEdges==CastAir);
 g.tick(castWindupMs-1,false,false,0);assert(!g.soundEdges);
 g.tick(1,false,false,0);assert(g.soundEdges==SpoolRelease);
 g.tick(castDurationMs-castWindupMs-1,false,false,0);assert(!g.soundEdges);
 g.tick(1,false,false,0);assert(g.soundEdges==WaterImpact&&g.sprayAge==0);
 g.enter(Phase::Fight);g.fish=0;g.target=g.line=12;g.sprayAge=500;
 bool churn=false;for(int i=0;i<150&&g.phase==Phase::Fight;i++){g.tick(25,false,false,.025f);if(g.soundEdges&RetrieveSplash){churn=true;break;}}
 assert(churn&&g.sprayAge==0);g.tick(16,false,false,.01f);assert(!(g.soundEdges&RetrieveSplash));
 g.heat=.99f;g.tick(10,false,false,2);assert(g.reason==Reason::Snapped&&g.soundEdges==BrokenLine);
 g.tick(16,false,false,0);assert(!g.soundEdges);
 SoundSettings s;s.music=3;s.volume=0;s.reelVolume=s.cueVolume=3;
 std::set<std::vector<int16_t>> heard;
 for(auto event:{CastAir,SpoolRelease,WaterImpact,RetrieveSplash,BrokenLine}){
  for(int muted=0;muted<=1;muted++){
   CreekSynth mixer;mixer.begin();auto mix=s;
   if(muted){if(event==SpoolRelease)mix.reelVolume=0;else mix.cueVolume=0;}
   std::vector<int16_t> pcm(2*16000);
   mixer.render(pcm.data(),16000,mix,false,false,0,{},event);
   int peak=0;for(size_t i=0;i<pcm.size();i+=2){assert(pcm[i]==pcm[i+1]);peak=std::max(peak,std::abs(int(pcm[i])));}
   assert(muted?peak==0:peak>800&&peak<32000);if(!muted)heard.insert(pcm);
   assert(std::all_of(pcm.end()-1500,pcm.end(),[](int n){return n==0;}));
  }
 }
 assert(heard.size()==5);
 if(argc>1){ // Write raw mono PCM from the production mixer for the listening sample.
  auto f=std::fopen(argv[1],"wb");assert(f);CreekSynth m;m.begin();
  const int cues[][2]={{0,CastAir},{180,SpoolRelease},{900,WaterImpact},{1800,RetrieveSplash},{2240,RetrieveSplash},{2800,BrokenLine}};
  for(int ms=0;ms<3400;ms++){int edges=0;for(auto &cue:cues)if(ms==cue[0])edges=cue[1];
   int16_t stereo[32];m.render(stereo,16,s,false,false,0,{},edges);for(int i=0;i<32;i+=2)std::fwrite(stereo+i,2,1,f);}
  std::fclose(f);
 }
 std::puts("PASS wind-up, payout, contact, cadence-limited retrieve, one-shot snap and five distinct gain-controlled stereo effects");
}