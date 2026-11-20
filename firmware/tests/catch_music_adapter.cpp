// Compile separately (do not also link bench.cpp). Exercise the actual adapter
// exports with seeded gameplay setup, then let normal advance() create edges.
#include "bench.cpp"
#include <cassert>
#include <cstdio>

static void setup(int music=2){
 initialize(817);config(music,2,0,2);place(8,0);reelVolume(0);
}
static void land(){
 g.fish=0;g.length=catalog[0].low;g.emptyCast=false;
 g.recoverMs=2000;g.runMs=1500;g.slackMs=500;
 g.target=8.f;g.line=0.f;g.heat=0;g.idle=0;g.slack=0;
 g.enter(Phase::Fight);
 advance(1,0,0,0);
 assert(g.phase==Phase::Landed && landingPending.active());
}
static void bite(){
 g.fish=0;g.emptyCast=false;g.rig=Technique::Float;
 g.enter(Phase::Waiting);g.waitMs=1;advance(1,0,0,0);
 assert(g.phase==Phase::Bite && cuePending);
}
static void blocks(unsigned n){
 for(unsigned i=0;i<n;++i)samples();
}
int main(){
 using locationaudio::MusicKind;
 // Suspended browser: land -> per-frame interruption clear -> resume held.
 setup();land();clearFishingSound();blocks(4);
 assert(g.phase==Phase::Landed && !g.filed);
 assert(synth.musicKind()==MusicKind::Location);

 // Clearing an already-playing reward releases it without resuming the cue.
 setup();land();blocks(4);assert(synth.musicKind()==MusicKind::Reward);
 clearFishingSound();blocks(4);assert(synth.musicKind()==MusicKind::Location);

 // Interruption clear must not steal the next real gameplay edge.
 setup();clearFishingSound();land();blocks(4);
 assert(synth.musicKind()==MusicKind::Reward);
 assert(fileCatch());blocks(4);
 assert(g.filed && synth.musicKind()==MusicKind::Location);

 // A missed bite in a suspended graph cannot sound when playback resumes.
 setup(3);bite();advance(2000,0,0,0);
 assert(g.phase==Phase::Lost && !cuePending);
 auto missed=samples();
 for(unsigned i=0;i<512;++i)assert(missed[i]==0);

 setup(3);clearFishingSound();bite();blocks(1);
 auto current=samples();
 assert(std::any_of(current,current+512,[](int16_t x){return x!=0;}));
 std::puts("Actual bench adapter: stale/active rewards, missed/live bite and deliberate filing passed");
}
