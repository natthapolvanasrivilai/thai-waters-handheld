#include "../WillowCreek/Synth.h"
#include <cassert>
#include <cstdio>
#include <vector>

using locationaudio::MusicKind;
static std::vector<int16_t> pcm(CreekSynth& synth,unsigned n,bool engaged,
  bool lost=false,bool held=false,creek::LandingCue edge={}){
 SoundSettings s;s.music=2;s.arrangement=8;
 std::vector<int16_t> out(n*2);
 synth.render(out.data(),n,s,engaged,false,0,edge,0,held,false,lost);
 return out;
}
int main(){
 constexpr auto fade=locationaudio::releaseSamples;
 constexpr auto intro=locationaudio::fightPickupSamples;
 constexpr auto outro=locationaudio::fightExitSamples;
 CreekSynth synth;synth.begin();pcm(synth,1000,false);
 pcm(synth,fade,true);
 assert(synth.musicKind()==MusicKind::Action);
 pcm(synth,intro+1000,true);
 pcm(synth,fade,true);
 assert(synth.musicKind()==MusicKind::Action);
 pcm(synth,fade,false,true);
 assert(synth.musicKind()==MusicKind::ActionTail);
 auto tail=pcm(synth,outro,false,true);
 assert(tail.front()==0 && tail.back()==0);
 assert(std::any_of(tail.begin(),tail.end(),[](auto x){return x!=0;}));
 assert(synth.musicKind()==MusicKind::Location);
 pcm(synth,1024,false,true);
 assert(synth.musicKind()==MusicKind::Location); // persistent Lost doesn't restart the tail

 synth.begin();pcm(synth,intro+4096,true);
 pcm(synth,fade,false,true,true,{5});
 assert(synth.musicKind()==MusicKind::Reward); // no loss-tail delay or overlay
 synth.begin();pcm(synth,intro+4096,true);
 pcm(synth,fade,false,false);
 assert(synth.musicKind()==MusicKind::Location); // non-loss interruption
 synth.begin();pcm(synth,intro+4096,true);
 pcm(synth,fade+200,false,true);assert(synth.musicKind()==MusicKind::ActionTail);
 pcm(synth,fade,true);assert(synth.musicKind()==MusicKind::Action); // fresh fight preempts tail
 std::puts("Pickup, terminal cadence, direct reward and interruption succeeded");
}
