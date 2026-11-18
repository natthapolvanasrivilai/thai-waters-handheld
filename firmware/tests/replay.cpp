#include "../WillowCreek/Creek.h"
#include "../WillowCreek/Score.h"
#include "../WillowCreek/Sound.h"
#include <cassert>
#include <cstdio>
using namespace creek;
static void check(bool test,const char* name){
  if(!test){std::fprintf(stderr,"FAILED %s\n",name);std::exit(1);}
  std::printf("PASS %s\n",name);
}
static void bite(Game& g) {
 g.tick(16,true,false,0);g.tick(650,false,false,0);g.tick(g.waitMs,false,false,0);
}
int main(){
 Calibration c{{0,0,1},{0,.6f,.8f}};
 check(c.valid()&&std::abs(c.tilt(c.raised)-36.8699f)<.001 && !Calibration{}.valid(),"two-pose calibration and missing-pose rejection");
 Calibration flipped{{0,0,-1},{-.6f,0,-.8f}};
 check(flipped.valid()&&std::abs(flipped.tilt(flipped.raised)-c.span())<.001,"reversed board axis yields the same raised angle");
 Gesture r;r.sample(0,40,0);r.sample(36,40,200);check(r.rise,"fresh lift");r.sample(35,40,250);check(!r.rise,"held rod cannot issue another hook");
 r.sample(1,40,420);check(r.cast,"raised rod swept back to playing pose casts");
 r.sample(35,40,900);r.sample(12,40,1100);r.sample(1,40,2000);check(!r.cast,"slow return cannot cast");
 Wheel w;w.read(4080,true,100,false);
 check(w.read(16,true,120,false)==32/4096.f,"forward wrap");check(w.read(4080,true,140,false)==-32/4096.f,"backward wrap");
 check(w.read(16,true,160,true)==-32/4096.f,"persistable reverse mapping");
 w.read(0,false,180,false);check(w.read(2400,true,220,false)==0,"lost magnet re-acquires without phantom turn");
 check(w.read(3900,true,232,false)==0 && w.read(10,true,500,false)==0,"implausible jump and stale sample ignored");
 Game g;g.seed=5359;bite(g);check(g.phase==Phase::Bite,"cast enters flight, waits, and bites");
 g.tick(60,false,true,0);check(g.phase==Phase::Fight,"fresh lift in bite window hooks");
 // Exercise the input chain. Deliver 1 physical turn/s in small wrapped encoder increments.
 Wheel knob;unsigned t=100,raw=4000;knob.read(raw,true,t,false);
 for(int i=0;i<1500 && g.phase==Phase::Fight;i++){
   t+=16;raw=(raw+(g.surge()?0:65))%4096;g.tick(16,false,false,knob.read(raw,true,t,false));
 }
 check(g.phase==Phase::Landed && g.catches==1,"wrapped encoder trace lands one fish");
 bite(g);g.tick(1451,false,true,0);check(g.phase==Phase::Lost && g.reason==Reason::Late,"expired window beats late lift");
 g.tick(16,true,false,0);g.tick(650,false,false,0);g.tick(30,false,true,0);
 check(g.reason==Reason::Early && g.phase==Phase::Lost,"early strike and recast");
 bite(g);g.tick(1,false,true,0);float line=g.line;g.tick(16,false,false,-.25f);
 check(g.line>line,"wrong-way winding pays line back");
 for(int i=0;i<600 && g.phase==Phase::Fight;i++)g.tick(16,false,false,0);
 check(g.reason==Reason::Escaped,"abandoned fight escapes");
 bite(g);g.tick(10,false,true,0);g.age=g.recoverMs;
 for(int i=0;i<65 && g.phase==Phase::Fight;i++)g.tick(16,false,false,.075f);
 check(g.reason==Reason::Snapped,"fast reeling on a surge breaks the line");
 for(int i=1;i<100;i++){Game a;a.seed=i;bite(a);a.tick(12,false,true,0);for(int k=0;k<3000 && a.phase==Phase::Fight;k++)a.tick(16,false,false,a.surge()?0.f:.020f);assert(a.phase==Phase::Landed);}
 check(true,"99 single-creek catch and replay scenarios");
 for(int j=0;j<4;j++)for(unsigned i=0;i<songSizes[j];i++){
   const auto& n=songs[j][i];assert(n.voice<4 && n.start+n.duration<=songEnds[j]);if(i)assert(n.start>=songs[j][i-1].start);}
 check(true,"four complete ordered location scores");
}
