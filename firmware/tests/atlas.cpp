#include "../WillowCreek/Rumble.h"
#include <cassert>
#include <cstdio>
#include <cstring>
using namespace creek;
int main(){
 int counts[fishCount]{};
 for(int i=0;i<siteCount;i++)for(int time=0;time<4;time++){
  Game g;g.site=i;g.timeSlot=time;int seen[fishCount]{};
  for(int k=0;k<12500;k++){
   g.enter(Phase::Ready);g.tick(16,true,false,0);
   assert(waterOf(g.fish)==i&&encounterWeight(g.fish,time)>0);
   assert(g.length>=catalog[g.fish].low&&g.length<=catalog[g.fish].high&&weightGrams(g.fish,g.length)>0);++seen[g.fish];++counts[g.fish];
  }
  for(int k=0;k<stockSize(i);k++){int id=stockId(i,k);assert((seen[id]>0)==(encounterWeight(id,time)>0));}
 }
 for(int n:counts)assert(n>0);
 for(int id:{prawn,ray}){Game x;x.fish=id;x.enter(Phase::Bite);x.tick(id==prawn?821:1151,false,true,0);assert(x.reason==Reason::Late);
  x.enter(Phase::Bite);x.tick(300,false,true,0);x.target=x.line=14;
  for(int n=0;n<4000&&x.phase==Phase::Fight;n++)x.tick(16,false,false,x.surge()?0.f:.02f);
  assert(x.phase==Phase::Landed);
 }
 Game g;auto& p=g.progress;
 assert(p.points()==0 && !p.upgrade(0));
 auto catchFish=[&](int id,int length){g.phase=Phase::Fight;g.fish=id;g.length=length;g.line=.01f;g.target=6;g.tick(16,false,false,.1f);assert(g.phase==Phase::Landed);};
 catchFish(0,21);assert(g.pointsAwarded==1 && p.book.discovered()==1 && p.chapter()==1);
 catchFish(0,16);assert(!g.newEntry && !g.personalBest && p.book.entries[0].count==2 && p.book.entries[0].best==21);
 assert(p.upgrade(0)&&p.points()==0&&!p.upgrade(0));
 g.enter(Phase::Bite);g.tick(1530,false,true,0);assert(g.phase==Phase::Fight);
 p.retrain();assert(p.points()==1&&p.upgrade(1));g.line=3;g.heat=0;g.tick(0,false,false,.5f);assert(std::abs(g.line-2.44f)<.001);
 p.retrain();assert(p.upgrade(2));g.heat=0;g.tick(0,false,false,.5f);assert(std::abs(g.heat-.09f)<.001);
 for(int i=1;i<fishCount;i++)catchFish(i,catalog[i].low);
 assert(p.book.discovered()==fishCount && p.waters()==5 && p.chapter()==5 && p.points()==17);
 p.retrain();assert(p.points()==18);assert(p.upgrade(0)&&p.upgrade(0)&&p.upgrade(0)&&!p.upgrade(0));
 Progress loaded;memcpy(&loaded,&p,sizeof(p));assert(loaded.points()==12&&loaded.book.entries[0].count==2);
 RumblePlan plan;g.enter(Phase::Waiting);g.waitMs=3500;g.age=2550;
 assert(plan.tick(g,2500,true)==Pulse::Tease && plan.tick(g,2520,true)==Pulse::None);
 g.enter(Phase::Bite);assert(plan.tick(g,3300,true)==Pulse::Bite && plan.tick(g,3320,true)==Pulse::None);
 g.enter(Phase::Fight);g.heat=.98;assert(plan.tick(g,5330,true)==Pulse::Pull);
 assert(plan.tick(g,8000,false)==Pulse::None);
 puts("PASS 250000 weighted casts in 20 habitat/time combinations, all 52 species, special hook windows and successful ray/prawn fights, record book, chapter gates, point accounting, three effective upgrades, refund, persistence layout and distinct tease/bite/pull events.");
}
