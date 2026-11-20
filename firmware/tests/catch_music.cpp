#include "../WillowCreek/Synth.h"
#include <cassert>
#include <set>
#include <vector>
#include <cstdio>

using creek::LandingCue;
static constexpr unsigned fade=locationaudio::releaseSamples;
static std::vector<int16_t> pcm(CreekSynth& synth, const SoundSettings& s, unsigned n,
 bool action=false, bool held=false, LandingCue edge={}){
 std::vector<int16_t> out(2*n);synth.render(out.data(),n,s,action,false,0,edge,0,held);return out;
}
int main(){
 SoundSettings s;s.arrangement=8;s.music=2;
 CreekSynth old,out,fresh;
 old.begin();out.begin();fresh.begin();
 assert(pcm(out,s,16000)==pcm(old,s,16000));
 const auto tail=pcm(old,s,fade);
 const auto switchIn=pcm(out,s,fade+4096,true);
 auto opening=pcm(fresh,s,4096,true);
 for(unsigned i=0;i<2*fade;++i)assert(switchIn[i]==tail[i]*int(fade-i/2)/int(fade));
 assert(std::equal(opening.begin(),opening.end(),switchIn.begin()+2*fade));
 // Bite and Fight are one engagement: no new score onset on the sustained level.
 assert(pcm(out,s,10000,true)==pcm(fresh,s,10000,true));
 const auto fightTail=pcm(fresh,s,fade,true);
 const auto fall=pcm(out,s,fade+4096);
 for(unsigned i=0;i<2*fade;++i)assert(fall[i]==fightTail[i]*int(fade-i/2)/int(fade));
 CreekSynth location;location.begin();opening=pcm(location,s,4096);
 assert(std::equal(opening.begin(),opening.end(),fall.begin()+2*fade));

 std::set<std::vector<int16_t>> tiers;
 for(unsigned char i=0;i<6;++i){
   CreekSynth t;t.begin();
   const auto clip=pcm(t,s,72000,true,true,{i});
   assert(tiers.insert(clip).second);
   assert(clip==[&]{CreekSynth r;r.begin();return pcm(r,s,72000,true,true,{i});}());
   assert(t.musicKind()==locationaudio::MusicKind::Action); // reward completed, fight still requested
 }
 // While a reward is sounding, the request is privileged over a still-active action.
 CreekSynth r;r.begin();pcm(r,s,4096,true,true,{5});
 assert(r.musicKind()==locationaudio::MusicKind::Reward);
 pcm(r,s,fade+1,false,false);
 assert(r.musicKind()==locationaudio::MusicKind::Location);
 // A completed catch cue returns to location and does not retrigger while held.
 r.begin();pcm(r,s,72000,false,true,{5});assert(r.musicKind()==locationaudio::MusicKind::Location);
 pcm(r,s,72000,false,true);assert(r.musicKind()==locationaudio::MusicKind::Location);
 // Enabled rewards are the acoustic score alone, not the legacy tone over it.
 r.begin();
 const auto rendered=pcm(r,s,20000,false,true,{4});
 locationaudio::Score score;score.rewardContext(true,4);
 int16_t sine[256]{};
 for(int i=0;i<256;++i)sine[i]=std::lround(std::sin(i*6.2831853f/256)*32760);
 for(unsigned i=0;i<rendered.size()/2;++i)
   assert(rendered[2*i]==score.sample(s.arrangement,sine,s.music,s.volume,false,false));
 // Clearing a pending reward midway through a fade must not start it.
 r.begin();pcm(r,s,2048,true);pcm(r,s,40,false,true,{5});pcm(r,s,fade,false,false);
 assert(r.musicKind()==locationaudio::MusicKind::Location);
 // Restoring/holding a catch is not a new reward, and visual cues stay visual.
 r.begin();pcm(r,s,8192,false,true);assert(r.musicKind()==locationaudio::MusicKind::Location);
 s.cue=1;assert(pcm(r,s,8192,true,true,{5})==[&]{CreekSynth q;q.begin();SoundSettings b=s;pcm(q,b,8192,false,true);return pcm(q,b,8192,true,true);}());
 // Controllers/players with Music Off still hear their original cue when allowed.
 s.music=3;s.cue=0;r.begin();
 const auto silent=pcm(r,s,4096,true);
 for(auto x:silent)assert(x==0);
 const auto fallback=pcm(r,s,4096,false,true,{5});
 assert(std::any_of(fallback.begin(),fallback.end(),[](int16_t x){return x;}));
 r.begin();for(auto x:pcm(r,s,256))assert(x==0);
 std::puts("Bite/fight continuity, exclusive transitions, 6 unique rewards, cancellation, visual and controller fallback passed");
}
