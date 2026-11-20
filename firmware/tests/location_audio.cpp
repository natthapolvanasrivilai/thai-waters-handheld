#include "../WillowCreek/Synth.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <set>
#include <vector>

static std::vector<int16_t> render(CreekSynth& synth, SoundSettings s, size_t frames, size_t block=128){
  std::vector<int16_t> pcm(2*frames);
  for(size_t i=0;i<frames;i+=block)
    synth.render(pcm.data()+2*i,std::min(block,frames-i),s,false,false);
  return pcm;
}
int main(){
  SoundSettings s;s.music=2; // prove the music differs even with ambience removed
  std::set<uint64_t> hashes;
  for(unsigned id=0; id<locationaudio::destinationCount; ++id){
    CreekSynth synth;synth.begin();s.arrangement=id;
    const auto pcm=render(synth,s,48000);
    assert(synth.locationId()==id);
    uint64_t hash=14695981039346656037ull;unsigned peak=0;
    for(int i:pcm){hash=(hash^uint16_t(i))*1099511628211ull;peak=std::max(peak,unsigned(std::abs(i)));}
    assert(peak>250 && peak<24000);
    assert(hashes.insert(hash).second);
    synth.begin();assert(pcm==render(synth,s,48000,127));
  }
  CreekSynth synth, first, next;
  synth.begin();first.begin();next.begin();
  s.arrangement=8;render(synth,s,25600);render(first,s,25600);
  const auto old=render(first,s,locationaudio::releaseSamples);
  assert(std::any_of(old.begin(),old.end(),[](int16_t i){return i!=0;}));
  s.arrangement=5; // Same existing fishing pool as ID 8, but a different score.
  const auto switched=render(synth,s,locationaudio::releaseSamples+4096,73);
  const auto fresh=render(next,s,4096);
  for(unsigned i=0;i<locationaudio::releaseSamples;++i)
    assert(switched[2*i]==old[2*i]*int(locationaudio::releaseSamples-i)/int(locationaudio::releaseSamples));
  assert(std::equal(fresh.begin(),fresh.end(),switched.begin()+2*locationaudio::releaseSamples));

  // Rapid navigation takes only the latest requested location after release.
  s.arrangement=99;render(synth,s,locationaudio::releaseSamples/2);
  s.arrangement=2;render(synth,s,locationaudio::releaseSamples/2+1);
  assert(synth.locationId()==2);
  s.arrangement=255;render(synth,s,locationaudio::releaseSamples+1);assert(synth.locationId()==0);

  // Check the loop boundary while the creek mix is active.
  CreekSynth loop;loop.begin();s.arrangement=8;s.music=0;
  const unsigned loopFrames=48*(16000*30/76);
  const auto cycle=render(loop,s,loopFrames+1);
  assert(cycle[2*(loopFrames-1)]==0 && cycle[2*loopFrames]==0);
  s.music=3;for(int i:render(synth,s,48000))assert(i==0);
  s.music=0;s.volume=0;for(int i:render(synth,s,48000))assert(i==0);
  std::array<int16_t,2048> cue{};
  s.volume=0;s.cue=0;synth.render(cue.data(),cue.size()/2,s,false,true,0,{},1);
  assert(std::any_of(cue.begin(),cue.end(),[](int16_t i){return i!=0;}));
  std::printf("%zu distinct, deterministic destination score renders; exclusive transition, mute and cues passed\n",hashes.size());
}
