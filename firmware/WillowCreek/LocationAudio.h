#pragma once
#include "ScenicRecipes.h"
#include <algorithm>
#include <stdint.h>

namespace locationaudio {
constexpr unsigned sampleRate=16000;
constexpr unsigned releaseSamples=sampleRate/50; // the outgoing score alone fades for 20 ms
constexpr unsigned destinationCount=sizeof(scenery::recipes)/sizeof(scenery::recipes[0]);
enum class MusicKind : uint8_t { Location, Action, Reward, ActionTail };
constexpr unsigned fightTickSamples=sampleRate*15/128; // sixteenth notes at 128 BPM
constexpr unsigned fightPickupSamples=sampleRate*23/100;
constexpr unsigned fightExitSamples=sampleRate*66/100;
constexpr unsigned actionTrack=destinationCount;
constexpr unsigned rewardTrack=actionTrack+1;
constexpr unsigned rewardCount=6;
constexpr unsigned pickupTrack=rewardTrack+rewardCount;
constexpr unsigned exitTrack=pickupTrack+1;
constexpr unsigned noTrack=exitTrack+1;
enum class Instrument : uint8_t { Nylon, Mallet, Flute, Acoustic, Bowed };
struct Palette {Instrument instrument; uint8_t water, motion;};
constexpr Palette palette(scenery::Water water){
  using namespace scenery;
  switch(water){
    case Lake: case Marsh: return {Instrument::Mallet,26,1};
    case Gorge: case Karst: return {Instrument::Flute,39,3};
    case Estuary: case Gulf: case Island: case Headland: return {Instrument::Bowed,19,4};
    case Wide: return {Instrument::Acoustic,32,2};
    default: return {Instrument::Nylon,33,2};
  }
}

class Score {
  struct Event {uint32_t start=0, step=0; unsigned duration=0, level=0, voice=0;};
  struct Voice {uint32_t phase=0, step=0, life=0; unsigned age=0, duration=0; int level=0;};
  Event events[124]{};
  Voice voices[3]{};
  unsigned pressure=0;
  Palette scene{Instrument::Nylon,0,0};
  unsigned id=noTrack, reward=rewardCount, length=0, clock=0, cursor=0, count=0, release=0;
  uint32_t noise=1, swell=0;
  int body=0, slow=0;

  static uint32_t hash(uint32_t x) {
    x=(x^(x>>16))*0x7feb352du;
    x=(x^(x>>15))*0x846ca68bu;
    return x^(x>>16);
  }
  static uint32_t step(unsigned centihz){return uint32_t((uint64_t(centihz)<<32)/(100*sampleRate));}
  // Six 4/4 bars: memorable opening, repeated/varied answer, and a cadence.
  // Note positions and durations are in eighth notes; pitch is MIDI.
  struct Note {uint8_t at, midi, gate;};
  static constexpr unsigned loopEighths=48;
  static constexpr unsigned referenceEighth(unsigned bpm){
    return sampleRate*30/bpm;
  }
  void add(unsigned at,unsigned lengthSamples,unsigned centihz,unsigned level,unsigned voice){
    // Insertion sort at score start only; no work/allocation in steady state.
    unsigned i=count++;
    while(i && events[i-1].start>at){events[i]=events[i-1];--i;}
    events[i]={at,step(centihz),lengthSamples,level,voice};
  }
  template<unsigned N>
  void addPhrase(const Note (&notes)[N],unsigned eighth,int transpose,unsigned level,unsigned voice){
    static constexpr unsigned centihz[]={6541,6930,7342,7778,8241,8731,9250,9800,10383,11000,
      11654,12347,13081,13859,14683,15556,16481,17461,18500,19600,
      20765,22000,23308,24694,26163,27718,29366,31113,32963,34923,
      36999,39200,41530,44000,46616,49388,52325,55437,58733,62225,
      65926,69846,73999,78399,83061,88000,93233,98777,104650};
    for(const auto n:notes){
      const unsigned accent=n.at%8==0?level:level*4/5;
      add(n.at*eighth,n.gate*eighth,centihz[int(n.midi)+transpose-36],accent,voice);
    }
  }
  void catchTheme(unsigned track){
    scene={Instrument::Acoustic,0,0};
    if(track==pickupTrack){
      // Soft low string and A–C# pickup into the established D minor hook.
      scene.instrument=Instrument::Nylon;
      length=fightPickupSamples;
      add(0,2200,11000,2100,1);
      add(430,1560,44000,3400,0);
      add(2050,1560,55437,4600,0);
      return;
    }
    if(track==exitTrack){
      // A quiet falling F–E–D resolution for a missed or escaped fish.
      // The tonic and the low D decay to silence before the place resumes.
      scene.instrument=Instrument::Nylon;
      length=fightExitSamples;
      add(0,2330,34923,4650,0);
      add(2580,2040,32963,3900,0);
      add(4790,5650,29366,4000,0);
      add(4870,5570,14683,3000,1);
      return;
    }
    if(track==actionTrack){
      // D minor: Dm–Bb–F–C / Gm–Bb–A7–Dm. Opening and answer vary
      // the hook before an A7 pull and a deliberate D minor resolution.
      // Sixteenth-note notation. One arrangement, three acoustic voices.
      static constexpr Note hook[]={
        {0,62,3},{3,65,2},{6,69,3},{10,72,2},{13,69,3},
        {16,70,3},{20,69,2},{23,65,3},{28,62,3},
        {32,65,3},{35,69,2},{38,72,4},{44,77,2},{47,76,1},
        {48,74,3},{52,72,2},{55,67,3},{60,64,3},
        {64,67,2},{67,70,2},{70,74,3},{74,77,2},{77,74,3},
        {80,82,3},{84,77,2},{87,74,3},{92,70,3},
        {96,69,2},{99,73,2},{102,76,3},{106,79,2},{109,76,3},
        {112,74,3},{116,77,2},{119,81,3},{124,74,4}
      };
      static constexpr uint8_t bass[]={38,46,41,48,43,46,45,38};
      static constexpr uint8_t inner[][3]={
        {57,62,65},{58,62,65},{57,60,65},{55,60,64},
        {55,58,62},{58,62,65},{57,61,67},{57,62,65}
      };
      length=128*fightTickSamples;
      addPhrase(hook,fightTickSamples,0,9300,0);
      for(unsigned bar=0;bar<8;++bar){
        const unsigned start=16*bar;
        const Note low[]={{uint8_t(start),bass[bar],4},{uint8_t(start+5),bass[bar],2},
          {uint8_t(start+8),uint8_t(bass[bar]+7),4},{uint8_t(start+13),uint8_t(bass[bar]+12),2}};
        const Note picking[]={{uint8_t(start+2),inner[bar][0],2},{uint8_t(start+6),inner[bar][1],2},
          {uint8_t(start+10),inner[bar][2],2},{uint8_t(start+14),inner[bar][1],2}};
        addPhrase(low,fightTickSamples,0,5400,1);
        addPhrase(picking,fightTickSamples,0,5200,2);
      }
      return;
    }
    // Successive rarities climb to broader openings and longer resolutions.
    static constexpr Note common[]={{0,66,1},{1,62,3}};
    static constexpr Note uncommon[]={{0,64,1},{1,66,1},{2,62,3}};
    static constexpr Note rare[]={{0,62,1},{1,66,1},{2,69,2},{4,66,1},{5,62,3}};
    static constexpr Note epic[]={{0,62,1},{1,66,1},{2,69,1},{3,74,2},{5,73,1},{6,74,4}};
    static constexpr Note legendary[]={{0,66,1},{1,69,1},{2,71,1},{3,74,2},{5,76,1},{6,73,2},{8,74,5}};
    static constexpr Note mythic[]={{0,62,1},{1,66,1},{2,69,1},{3,74,2},{5,76,1},{6,78,2},{8,76,1},{9,73,1},{10,74,6}};
    static constexpr unsigned ending[]={4,5,8,10,13,16};
    static constexpr unsigned resolution[]={0,0,0,6,8,10};
    const unsigned tier=track-rewardTrack,eighth=referenceEighth(112);
    length=ending[tier]*eighth+eighth/2;
    scene.instrument=Instrument::Nylon;
    const unsigned gain=7600+tier*210;
    switch(tier){
      case 0:addPhrase(common,eighth,0,gain,0);break;
      case 1:addPhrase(uncommon,eighth,0,gain,0);break;
      case 2:addPhrase(rare,eighth,0,gain,0);break;
      case 3:addPhrase(epic,eighth,0,gain,0);break;
      case 4:addPhrase(legendary,eighth,0,gain,0);break;
      case 5:addPhrase(mythic,eighth,0,gain,0);break;
    }
    add(0,4*eighth,14683u,gain/4,1); // low D
    if(tier>=3)add(resolution[tier]*eighth,(ending[tier]-resolution[tier])*eighth,14683u,gain/3,1);
  }
  void start(unsigned place){
    id=place;
    clock=cursor=count=release=0;for(auto& v:voices)v={};
    noise=hash(id+411u);if(!noise)noise=1;
    body=slow=0;swell=0;
    pressure=0;
    if(id>=actionTrack){catchTheme(id);return;}
    scene=palette(scenery::recipes[id].water);
    if(id==8)scene.water=58; // match the approved creek music/water balance
    // Same transcription as the creek, lake, gorge and coastal listening demos.
    static constexpr Note creekLead[]={
      {0,62,2},{2,66,2},{4,69,3},{8,71,2},{10,69,2},{12,66,3},
      {16,62,2},{18,66,2},{20,69,2},{22,74,2},{24,73,2},{26,69,2},
      {28,66,3},{32,64,2},{34,67,2},{36,69,2},{38,73,2},{40,74,5},
      {46,62,2}
    };
    static constexpr Note creekSupport[]={
      {0,50,3},{4,57,3},{8,47,3},{12,54,3},{16,43,3},{20,50,3},
      {24,42,3},{28,50,3},{32,45,3},{36,55,3},{40,50,5},{46,54,2}
    };
    static constexpr Note lakeLead[]={
      {0,69,2},{2,67,1},{3,65,2},{6,72,2},{8,69,2},{10,65,2},
      {12,62,3},{16,69,2},{18,67,1},{19,65,2},{22,74,2},{24,72,3},
      {28,69,3},{32,67,2},{34,70,2},{36,76,2},{38,67,2},{40,65,6}
    };
    static constexpr Note lakeSupport[]={
      {0,53,3},{6,60,2},{8,50,3},{16,46,3},{22,53,2},{24,45,4},
      {32,48,3},{36,58,2},{40,53,5}
    };
    static constexpr Note gorgeLead[]={
      {0,69,3},{3,72,2},{5,74,2},{8,76,3},{11,74,2},{13,72,2},
      {16,69,3},{19,72,2},{21,74,2},{24,76,3},{27,77,2},{29,76,2},
      {32,74,3},{35,71,2},{37,68,2},{40,69,7}
    };
    static constexpr Note wideLead[]={
      {0,60,2},{2,62,2},{4,64,2},{6,67,2},{8,69,3},{11,67,1},
      {12,64,3},{16,60,2},{18,62,2},{20,64,2},{22,72,2},{24,71,2},
      {26,67,2},{28,64,3},{32,65,2},{34,69,2},{36,67,2},{38,62,2},
      {40,60,7}
    };
    static constexpr Note wideSupport[]={
      {0,48,3},{4,55,3},{8,45,3},{12,52,3},{16,53,3},{20,57,3},
      {24,52,3},{28,55,3},{32,43,3},{36,59,2},{40,48,7}
    };
    static constexpr Note seaLead[]={
      {0,55,3},{3,59,2},{5,62,3},{8,64,3},{11,62,2},{13,59,3},
      {16,55,3},{19,59,2},{21,62,3},{24,67,3},{27,66,2},{29,62,3},
      {32,60,3},{35,57,2},{37,66,3},{40,67,7}
    };
    static constexpr Note seaSupport[]={
      {0,43,7},{8,40,7},{16,48,7},{24,47,7},{32,50,7},{40,43,7}
    };
    unsigned eighth=6520+id*11; // stable, unique per-location tempo
    int transpose=int((id+unsigned(scenery::recipes[id].feature)*2)%9)-4;
    if(id==8 || id==0 || id==4 || id==99){
      transpose=0;
      eighth=referenceEighth(id==8?76:id==0?80:72);
    }
    length=loopEighths*eighth;
    const unsigned level=id==8?9500:6300;
    switch(scene.instrument){
      case Instrument::Nylon:
        addPhrase(creekLead,eighth,transpose,level,0);
        addPhrase(creekSupport,eighth,transpose,level/4,1);break;
      case Instrument::Mallet:
        addPhrase(lakeLead,eighth,transpose,level,0);
        addPhrase(lakeSupport,eighth,transpose,level/4,1);break;
      case Instrument::Flute:
        addPhrase(gorgeLead,eighth,transpose,level,0);break; // solo with breathing space
      case Instrument::Acoustic:
        addPhrase(wideLead,eighth,transpose,level,0);
        addPhrase(wideSupport,eighth,transpose,level/4,1);break;
      case Instrument::Bowed:
        addPhrase(seaLead,eighth,transpose,level,0);
        addPhrase(seaSupport,eighth,transpose,level/4,1);break;
    }
  }
  int voiceSample(Voice& v,const int16_t* sine){
    if(v.life==0 || v.age>=v.duration)return 0;
    const auto osc=[&](unsigned harmonic){return int(sine[(v.phase*harmonic)>>24]);};
    int wave=0;unsigned attack=160,decay=65526;
    int vibrato=0;
    const int bright=int(std::min<uint32_t>(v.life>>10,1024u));
    switch(scene.instrument){
      case Instrument::Nylon:
        wave=osc(1)*5/8+(osc(2)/5+osc(3)/13-osc(5)/26)*bright/1024;break;
      case Instrument::Mallet:
        wave=osc(1)*3/4+(osc(3)/8+osc(4)/14)*bright/1024;
        attack=96;decay=65520;break;
      case Instrument::Flute:
        wave=osc(1)*3/4+osc(2)/14+osc(3)/28;
        attack=1840;decay=65530;break;
      case Instrument::Acoustic:
        wave=osc(1)*3/5+(osc(2)/5+osc(3)/9+osc(4)/20+osc(5)/30)*bright/1024;
        attack=id==actionTrack?220:110;decay=65524;break;
      case Instrument::Bowed:
        // Soft string body, slowly opening articulation and unobtrusive vibrato.
        wave=osc(1)*2/3+(osc(2)/5+osc(3)/8+osc(4)/21)*bright/1024;
        attack=4500;decay=65532;
        vibrato=(int(sine[(v.age*1288490u)>>24])/4096)*int(v.step/2800u);
        break;
    }
    // Integer, fixed-rate envelopes; no per-sample transcendental functions.
    int env=int(v.life>>10)*int(std::min(v.age,attack))/int(attack);
    const unsigned tail=scene.instrument==Instrument::Bowed?1900:850;
    env=env*int(std::min(v.duration-v.age,tail))/int(tail);
    int value=(wave*v.level/32768)*env/1024;
    v.phase+=v.step+uint32_t(vibrato);++v.age;
    v.life-=(v.life*(65536u-decay)+65535u)>>16;
    return value;
  }
  int ambience(const int16_t* sine){
    noise=1664525u*noise+1013904223u;
    const int input=int(noise>>20)-2048;
    body+=(input-body)/4;
    slow+=(body-slow)/(scene.motion==4?32:16);
    // Slower ocean swells, with a little more breathing than inland water.
    swell+=scene.motion==4?40265u:79457u;
    const int wave=int(sine[swell>>24])/(scene.motion==4?384:512);
    const unsigned edge=std::min(1024u,std::min(clock,length-clock-1));
    return (((body-slow)*scene.water/64)*(176+wave)/256)*int(edge)/1024;
  }
public:
  unsigned locationId() const {return id;}
  MusicKind musicKind() const {
    if(id==exitTrack)return MusicKind::ActionTail;
    if(id==actionTrack || id==pickupTrack)return MusicKind::Action;
    return id>=rewardTrack && id<pickupTrack?MusicKind::Reward:MusicKind::Location;
  }
  void rewardContext(bool eligible,unsigned edge){
    if(!eligible)reward=rewardCount;
    else if(edge<rewardCount)reward=edge;
  }
  void reset(){*this=Score{};}
  int sample(unsigned requested,const int16_t* sine,unsigned music,unsigned volume,bool chase,bool duck,bool surge=false,bool lost=false){
    requested=requested<destinationCount?requested:0;
    const unsigned place=requested;
    const unsigned base=chase?(id==actionTrack?actionTrack:pickupTrack):place;
    const bool closeFight=lost && !chase && (id==actionTrack || id==pickupTrack || id==exitTrack);
    requested=reward<rewardCount?rewardTrack+reward:closeFight?exitTrack:base;
    if(id==noTrack)start(requested);
    if(id!=requested && !release)release=releaseSamples;
    while(cursor<count && events[cursor].start==clock){
      const auto e=events[cursor++];
      voices[e.voice]={0,e.step,1u<<20,0,e.duration,int(e.level)};
    }
    const int main=voiceSample(voices[0],sine), harmony=voiceSample(voices[1],sine);
    int bed=main+(music==1?harmony/3:harmony);
    if(id==actionTrack){
      // Articulate the picked parts over a short ramp when a fish runs.
      // The soundtrack contains notes only; bite, reel and foley are emitted
      // separately by game events in CreekSynth, never on musical beats.
      if(surge && pressure<2048)++pressure;
      else if(!surge && pressure>0)--pressure;
      const int picking=voiceSample(voices[2],sine);
      bed=main*(4096+int(pressure)*5/8)/4096+harmony+
        picking*(2400+int(pressure)*3/2)/4096;
    }
    if(id<actionTrack){
      if(music!=2)bed+=ambience(sine);else (void)ambience(sine);
    }
    int pcm=(music==3?0:bed*int(volume)/(duck?6:2));
    // Ambience state stays continuous across score loops. Ramp the whole bed
    // to silence at the boundary before voices reset, even for long strings.
    const unsigned edge=std::min(releaseSamples,std::min(clock,length-clock-1));
    pcm=pcm*int(edge)/int(releaseSamples);
    if(++clock==length){
      if(musicKind()==MusicKind::Reward){
        // A one-shot reaches silence naturally and never loops or replays
        // merely because the catch screen is still open.
        if(reward<rewardCount && id==rewardTrack+reward)reward=rewardCount;
        start(reward<rewardCount?rewardTrack+reward:base);
      }else if(id==pickupTrack){
        start(requested==pickupTrack?actionTrack:requested);
      }else if(id==exitTrack){
        start(requested==exitTrack?place:requested);
      }else{clock=cursor=0;for(auto& v:voices)v={};}
    }
    if(release){
      pcm=pcm*int(release)/int(releaseSamples);
      if(--release==0)start(requested);
    }
    return pcm;
  }
};
}
