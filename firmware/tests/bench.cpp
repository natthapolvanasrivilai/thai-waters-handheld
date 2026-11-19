#include "../WillowCreek/Creek.h"
#include "../WillowCreek/RodFeedback.h"
#include "../WillowCreek/Synth.h"
#include "../WillowCreek/SpecimenArt.h"
#include "../WillowCreek/Rumble.h"
#include "../WillowCreek/ReelDetents.h"
#include "../WillowCreek/Destinations.h"
using namespace creek;
static Game g;
static CreekSynth synth;
static SoundSettings s;
static int16_t stereo[512];
static bool cuePending=false;
static uint8_t waterSounds=0;
static LandingCue landingPending;
static RumblePlan tactile;
static ReelDetents detents;
static int crossedTeeth=0,clickPending=0;
#define EXPORT __attribute__((visibility("default")))
static uint8_t portrait[50][96];
static int portraitFrame=0;
extern "C" {
EXPORT int hasPortrait(int id){return specimen::has(id);}
EXPORT uint8_t* speciesPixels(int id){
 if(id<60||!specimen::has(id))return nullptr;
 portraitFrame=specimen::index[id];const auto& frame=specimen::frames[portraitFrame];
 for(int y=0;y<50;y++)for(int x=0;x<96;x++)portrait[y][x]=specimen::pixel(frame,x,y);
 return &portrait[0][0];
}
EXPORT const uint16_t* speciesInk(){return specimen::frames[portraitFrame].ink;}
EXPORT void initialize(unsigned seed){waterSounds=0;g=Game{};g.beginSession(seed);synth.begin();detents=ReelDetents{};tactile=RumblePlan{};cuePending=false;landingPending={};crossedTeeth=clickPending=0;}
EXPORT void advance(unsigned dt,int cast,int lift,float turns){
 auto before=g.phase;g.tick(dt,cast,lift,turns);waterSounds|=g.soundEdges;
 if(before!=g.phase && g.phase==Phase::Bite && s.cue!=1)cuePending=true;
 if(before!=g.phase && g.phase==Phase::Landed && s.cue!=1 && s.cueVolume)
   landingPending={catalog[g.fish].tier,g.landingReward()};
 if(g.phase!=Phase::Landed)landingPending={};
}
EXPORT int fileCatch(){
 // A suspended browser audio graph may never have consumed the reveal.
 landingPending={};waterSounds=0;synth.clearFoley();
 return g.fileCatch();
}
EXPORT int filed(){return g.filed;}
EXPORT int setBait(int choice){return g.setBait(choice);}
EXPORT int baitChoice(){return g.bait;}
EXPORT int baitScore(int id,int choice){
 return id>=0 && id<fishCount && choice>=0 && choice<baitCount?baitWeightFor(id,choice,int(g.rig)):0;
}
EXPORT int recommendedBait(int id){return id>=0 && id<fishCount?preferredChoice(id):0;}
EXPORT int landingReward(){return int(g.landingReward());}
EXPORT void restoreCatch(int fish,int length){
 if(validSavedSize(fish,length)){
   landingPending={};
   g.emptyCast=false;g.fish=fish;g.length=length;g.filed=false;g.enter(Phase::Landed);
 }
}
EXPORT int sprayAge(){return g.sprayAge;}
EXPORT int windupMs(){return castWindupMs;}
EXPORT int flightMs(){return castDurationMs;}
EXPORT void clearFishingSound(){waterSounds=0;synth.clearFoley();}
EXPORT int state(){return int(g.phase);}
EXPORT void setAim(float x,float y){g.setAim(x,y);}
EXPORT float aimX(){return g.aimX;}
EXPORT float aimY(){return g.aimY;}
EXPORT float zoneX(int kind){return g.castZone(kind).x;}
EXPORT float zoneY(int kind){return g.castZone(kind).y;}
EXPORT float zoneRX(int kind){return g.castZone(kind).rx;}
EXPORT float zoneRY(int kind){return g.castZone(kind).ry;}
EXPORT int featureAt(float x,float y){return g.featureAt(x,y);}
EXPORT void conditions(int mode,int month,unsigned day){
 if(mode<0 || mode>4 || month<1 || month>12 || g.running())return;
 g.weatherMode=mode;g.updateWeather(month,day);
}
EXPORT int weather(){return int(g.weather);}
EXPORT uint32_t tintColor(uint32_t color){return weatherTint(color,g.weather);}
static WeatherStroke skyFrame[maxWeatherStrokes];
EXPORT WeatherStroke* skyStrokes(){return skyFrame;}
EXPORT int sampleSky(unsigned ms){return weatherStrokes(skyFrame,g.weather,ms,g.destination,g.timeSlot);}
EXPORT int contact(){return g.contact;}
EXPORT int junkId(){return g.junkId;}
EXPORT float releaseProgress(){return g.releaseProgress();}
EXPORT void abandonCast(){g.abandonCast();}
EXPORT int reason(){return int(g.reason);}
EXPORT unsigned age(){return g.age;}
EXPORT int catches(){return g.catches;}
EXPORT int species(){return g.fish;}
EXPORT int noStock(){return g.emptyCast;}
EXPORT int lengthCm(){return g.length;}
EXPORT float remaining(){return g.line;}
EXPORT float fraction(){return g.target?g.line/g.target:1;}
EXPORT float tension(){return g.heat;}
EXPORT int surging(){return g.surge();}
EXPORT int fightBeat(){return int(g.beat());}
EXPORT int fightStyle(){return int(g.fightStyle());}
EXPORT int holdingBottom(){return g.holdingBottom();}
EXPORT float rodLoad(){return g.rodLoad();}
EXPORT float pullOffset(){return g.pullOffset();}
EXPORT const char* fightInstruction(){return creek::fightInstruction(g);}
EXPORT void setTechnique(int i){g.setRig(i);}
EXPORT int technique(){return int(g.rig);}
EXPORT int sinking(){return g.falling;}
EXPORT int rodUp(){return g.rodHeldHigh;}
EXPORT unsigned fallAge(){return g.age-g.fallStart;}
EXPORT int strokes(){return g.strokes;}
EXPORT int strokesNeeded(){return g.strokesNeeded;}
EXPORT float lureTravel(){return g.lureTurns;}
EXPORT void config(int mode,int volume,int cue,int fx){s.music=mode;s.volume=volume;s.cue=cue;s.cueVolume=fx;}
EXPORT void reelVolume(int level){if(level>=0&&level<=3)s.reelVolume=level;}
EXPORT int16_t* samples(){
 synth.render(stereo,256,s,g.phase==Phase::Fight,cuePending,clickPending,landingPending,waterSounds);waterSounds=0;
 cuePending=false;clickPending=0;landingPending={};return stereo;
}

EXPORT int speciesCount(){return fishCount;}
EXPORT int availableAt(int id,int place,int time){return livesHere(id,place,time);}
EXPORT int caught(int i){return i>=0 && i<fishCount?g.progress.book.entries[i].count:0;}
EXPORT int best(int i){return i>=0 && i<fishCount?g.progress.book.entries[i].best:0;}
EXPORT int pts(){return g.progress.points();}
EXPORT int chapter(){return g.progress.chapter();}
EXPORT int rank(int i){return g.progress.rank[i];}
EXPORT int purchase(int i){return g.progress.upgrade(i);}
EXPORT void refund(){g.progress.retrain();}
EXPORT void restoreEntry(int i,int n,int cm){
 if(i>=0 && i<fishCount && n>=0 && n<10000000 && ((n==0 && cm==0)||(n>0 && validSavedSize(i,cm)))){
  g.progress.book.entries[i].count=n;g.progress.book.entries[i].best=cm;}
}
EXPORT int grams(){return g.landedGrams;}
EXPORT const char* measurement(int id,int cm){return sizeLabel(id,cm);}
EXPORT void visit(int i,int t){if(i>=0&&i<siteCount&&t>=0&&t<4){if(g.site!=i||g.timeSlot!=t){g.enter(Phase::Ready);cuePending=false;}g.site=s.site=i;g.timeSlot=t;}}
EXPORT void place(int id,int t){if(id<0||id>=destinationCount||t<0||t>3)return;if(id!=g.destination){g.enter(Phase::Ready);cuePending=false;}g.arriveAt(id);visit(destinations[id].pool,t);s.site=destinations[id].pool%4;s.arrangement=id;}
static Calibration pose;static Gesture motion;static Vec rest;static bool calibrated=false;
EXPORT void restPose(float x,float y,float z){rest=unit({x,y,z});calibrated=false;motion=Gesture{};}
EXPORT int liftPose(float x,float y,float z){pose={rest,unit({x,y,z})};calibrated=pose.valid();return calibrated;}
EXPORT float angle(float x,float y,float z){return calibrated?pose.tilt(unit({x,y,z})):0;}
EXPORT int gesture(float deg,unsigned now){if(!calibrated)return 0;motion.sample(deg,pose.span(),now);g.rodHeldHigh=motion.high;return motion.cast?1:motion.rise?2:0;}
EXPORT void handheldRodHigh(int high){g.rodHeldHigh=high!=0;}
EXPORT void resetGesture(){motion=Gesture{};g.rodHeldHigh=false;}
EXPORT void travel(int i){if(i>=0 && i<siteCount){g.site=i;s.site=i;g.enter(Phase::Ready);cuePending=false;}}
static Wheel phoneDial;
EXPORT void resetDetents(){detents=ReelDetents{};crossedTeeth=clickPending=0;}
EXPORT float dialSample(int raw,unsigned now){
 bool good=raw>=0 && raw<=4095;
 float turns=phoneDial.read(raw,good,now,false);
 if(good)crossedTeeth+=detents.measure(turns);else resetDetents();
 return turns;
}
EXPORT void dialReset(){phoneDial=Wheel{};}
EXPORT int teasing(){return g.teasing();}
EXPORT int rumbleEvent(unsigned now,int active){
 Pulse fish=tactile.tick(g,now,active);
 if(!active){resetDetents();return int(Pulse::None);}
 int click=detents.feedback(crossedTeeth,fish,now);crossedTeeth=0;
 if(fish!=Pulse::None)clickPending=0;
 if(click){clickPending=click;return int(Pulse::Detent);}
 return int(fish);
}
EXPORT int award(){return g.pointsAwarded;}
EXPORT int fresh(){return g.newEntry;}
EXPORT int recordBest(){return g.personalBest;}
}

