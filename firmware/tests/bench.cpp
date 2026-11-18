#include "../WillowCreek/Creek.h"
#include "../WillowCreek/Synth.h"
#include "../WillowCreek/Destinations.h"
using namespace creek;
static Game g;
static CreekSynth synth;
static SoundSettings s;
static int16_t stereo[512];
static bool cuePending=false;
#define EXPORT __attribute__((visibility("default")))
extern "C" {
EXPORT void initialize(unsigned seed){g=Game{};g.seed=seed;synth.begin();}
EXPORT void advance(unsigned dt,int cast,int lift,float turns){
 auto before=g.phase;g.tick(dt,cast,lift,turns);
 if(before!=g.phase && g.phase==Phase::Bite && s.cue!=1)cuePending=true;
}
EXPORT int state(){return int(g.phase);}
EXPORT int reason(){return int(g.reason);}
EXPORT unsigned age(){return g.age;}
EXPORT int catches(){return g.catches;}
EXPORT int species(){return g.fish;}
EXPORT int lengthCm(){return g.length;}
EXPORT float remaining(){return g.line;}
EXPORT float fraction(){return g.target?g.line/g.target:1;}
EXPORT float tension(){return g.heat;}
EXPORT int surging(){return g.surge();}
EXPORT void config(int mode,int volume,int cue,int fx){s.music=mode;s.volume=volume;s.cue=cue;s.cueVolume=fx;}
EXPORT int16_t* samples(){synth.render(stereo,256,s,g.phase==Phase::Fight,cuePending);cuePending=false;return stereo;}

EXPORT int caught(int i){return g.progress.book.entries[i].count;}
EXPORT int best(int i){return g.progress.book.entries[i].best;}
EXPORT int pts(){return g.progress.points();}
EXPORT int chapter(){return g.progress.chapter();}
EXPORT int rank(int i){return g.progress.rank[i];}
EXPORT int purchase(int i){return g.progress.upgrade(i);}
EXPORT void refund(){g.progress.retrain();}
EXPORT void restoreEntry(int i,int n,int cm){
 if(i>=0 && i<fishCount && n>=0 && n<10000000 && ((n==0 && cm==0)||(n>0 && cm>=catalog[i].low && cm<=catalog[i].high))){
  g.progress.book.entries[i].count=n;g.progress.book.entries[i].best=cm;}
}
EXPORT int grams(){return weightGrams(g.fish,g.length);}
EXPORT void visit(int i,int t){if(i>=0&&i<siteCount&&t>=0&&t<4){if(g.site!=i||g.timeSlot!=t){g.enter(Phase::Ready);cuePending=false;}g.site=s.site=i;g.timeSlot=t;}}
EXPORT void place(int id,int t){if(id<0||id>=destinationCount)return;visit(destinations[id].pool,t);s.site=destinations[id].pool%4;s.arrangement=id;}
static Calibration pose;static Gesture motion;static Vec rest;static bool calibrated=false;
EXPORT void restPose(float x,float y,float z){rest=unit({x,y,z});calibrated=false;motion=Gesture{};}
EXPORT int liftPose(float x,float y,float z){pose={rest,unit({x,y,z})};calibrated=pose.valid();return calibrated;}
EXPORT float angle(float x,float y,float z){return calibrated?pose.tilt(unit({x,y,z})):0;}
EXPORT int gesture(float deg,unsigned now){if(!calibrated)return 0;motion.sample(deg,pose.span(),now);return motion.cast?1:motion.rise?2:0;}
EXPORT void resetGesture(){motion=Gesture{};}
EXPORT void travel(int i){if(i>=0 && i<siteCount){g.site=i;s.site=i;g.enter(Phase::Ready);cuePending=false;}}
static Wheel phoneDial; EXPORT float dialSample(int raw,unsigned now){return phoneDial.read(raw,raw>=0 && raw<=4095,now,false);} EXPORT void dialReset(){phoneDial=Wheel{};}
EXPORT int teasing(){return g.teasing();}
EXPORT int award(){return g.pointsAwarded;}
EXPORT int fresh(){return g.newEntry;}
EXPORT int recordBest(){return g.personalBest;}
}

