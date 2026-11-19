#include "../WillowCreek/Rumble.h"
#include <cassert>
#include <cstdio>
#include <cstring>
using namespace creek;
static void checkStock(){
 bool checkedEmptyCast=false;
 double smallestRegularChance=1.;
 for(int place=0;place<destinationCount;++place){
   Game g;g.beginSession(1);g.destination=place;g.arriveAt(place);g.site=destinations[place].pool;
   for(int t=0;t<4;++t)for(int bait=0;bait<baitCount;++bait)for(int rig=0;rig<3;++rig){
     g.timeSlot=t;g.bait=bait;g.rig=Technique(rig);
     int totals[2]{};
     bool hasMythic=false;
     for(int group=0;group<2;++group)g.visitCandidates(group,[&](int id){
       if(catalog[id].tier==5){if(g.drawWeight(id))hasMythic=true;}
       else totals[group]+=g.drawWeight(id);
     });
     if(!totals[0] && !totals[1] && !hasMythic && !checkedEmptyCast){
       for(int x=1;x<=9 && g.featureAt(g.aimX,g.aimY);++x)g.setAim(x*.1f,.72f);
       if(g.featureAt(g.aimX,g.aimY))continue;
       g.landedGrams=120;
       g.tick(16,true,false,0);
       assert(!g.landedGrams && g.landingReward()==LandingReward::Catch);
       assert(g.phase==Phase::Flight && g.emptyCast && g.length==0 && g.fish>=0);
       g.tick(creek::castDurationMs,false,false,0);
       assert(g.phase==Phase::Waiting && !g.teasing());
       g.tick(g.waitMs,true,true,1.f);
       assert(g.phase==Phase::Lost && g.reason==Reason::NoBite && !g.fileCatch() && !g.progress.book.discovered());
       checkedEmptyCast=true;
     }
     for(int group=0;group<2;++group){
       if(!totals[group])continue;
       const double groupChance=totals[1-group]?(group?1./3:2./3):1.;
       g.visitCandidates(group,[&](int id){
         if(catalog[id].tier==5 || !g.drawWeight(id))return;
         const double chance=groupChance*g.drawWeight(id)/totals[group];
         smallestRegularChance=std::min(smallestRegularChance,chance);
       });
     }
   }
 }
 assert(checkedEmptyCast && smallestRegularChance>1./16384.);
 int eligible=0;
 for(int id=0;id<fishCount;++id){
   if(!specimen::has(id)){Game missing;assert(missing.drawWeight(id)==0);continue;}
   ++eligible;
   const auto& f=catalog[id];
   Game g;g.site=waterOf(id);g.destination=f.spot;
   if(f.spot==255)for(int p=0;p<destinationCount;++p)if(destinations[p].pool==g.site){g.destination=p;break;}
   g.timeSlot=0;while(g.timeSlot<4 && !encounterWeight(id,g.timeSlot))++g.timeSlot;
   assert(g.timeSlot<4);g.bait=preferredChoice(id);
   for(int rig=1;rig<3 && !g.baitWeight(id);++rig)g.rig=Technique(rig);
   assert(g.baitWeight(id)>0);
   bool selected=false;
   for(uint32_t seed=1;seed<=500000 && !selected;++seed){g.seed=seed;selected=g.drawFish()==id;}
   assert(selected);
 }
 printf("PASS all %d illustrated species reachable through actual native draws, real no-stock cast expires with zero credit, rarest eligible regular odds 1/%.0f.\n",eligible,1./smallestRegularChance);
}
int main(){
 // Cards are optional for storage and for opening a saved journal. Removing
 // the available pixel bank must narrow the draw pool without renumbering it.
 const uint8_t* fullBank=specimen::cardPixels;
 specimen::cardPixels=nullptr;
 int cardOnly=0;
 for(int id=0;id<fishCount;++id){
   if(specimen::index[id]<specimen::residentFrames)continue;
   Game replay;
   assert(!specimen::has(id)&&replay.drawWeight(id)==0);
   replay.fish=id;replay.length=catalog[id].low;replay.enter(Phase::Landed);
   assert(replay.fileCatch()&&replay.progress.book.entries[id].count==1);
   ++cardOnly;
 }
 assert(cardOnly>0&&specimen::has(1822));
 specimen::cardPixels=fullBank;
 checkStock();
 // Scientific reference points, the full catalog range, and old ray saves.
 assert(weightGrams(43,12)==20 && weightGrams(prawn,12)==17 && weightGrams(1,12)==27);
 assert(weightGrams(ray,200)==260196 && weightGrams(51,188)==37979);
 // Authored shapes at equal length, and a large river fish without overflow.
 assert(weightGrams(49,100)==6888 && weightGrams(50,100)==20622 && weightGrams(39,225)==225730);
 assert(validSavedSize(ray,240) && !validSavedSize(ray,241) && !weightGrams(ray,240));
 assert(!strcmp(sizeLabel(ray,240),"Recorded size") && !strcmp(sizeLabel(ray,200),"Disc width"));
 for(int i=0;i<fishCount;i++){
   int previous=0;
   for(int cm=catalog[i].low;cm<=catalog[i].high;cm++){
     const int grams=weightGrams(i,cm);
     assert(grams>0 && grams>=previous);previous=grams;
   }
 }
 Game held;held.fish=prawn;held.length=12;held.enter(Phase::Landed);
 const int savedGrams=held.landedGrams;
 Game resumed;resumed.fish=prawn;resumed.length=12;resumed.enter(Phase::Landed);
 assert(savedGrams==resumed.landedGrams && resumed.fileCatch() && resumed.landedGrams==savedGrams);
 int counts[originalSpecies]{};
 for(int i=0;i<siteCount;i++)for(int time=0;time<4;time++){
   Game g;g.site=i;g.timeSlot=time;
   for(int d=0;d<destinationCount;d++)if(destinations[d].pool==i){g.destination=d;break;}
   for(int k=0;k<12500;k++){
     g.bait=k%baitCount;g.rig=Technique((k/baitCount)%3);g.enter(Phase::Ready);g.tick(16,true,false,0);
     if(g.emptyCast)continue;
     assert(specimen::has(g.fish));
     assert(livesHere(g.fish,g.destination,time) && g.baitWeight(g.fish)>0);
     assert(validSavedSize(g.fish,g.length) && weightGrams(g.fish,g.length)>0);
     if(g.fish<originalSpecies)++counts[g.fish];
   }
 }
 for(int n:counts)assert(n>0);
 int mythics=0;
 for(int id=originalSpecies;id<fishCount;id++){
   const auto& f=catalog[id];assert(f.tier<=5 && f.timeMask && f.high>=f.low);
   if(f.tier==5){
     ++mythics;assert(f.spot<destinationCount && !(f.timeMask&(f.timeMask-1)));
     Game g;g.site=f.site;g.destination=f.spot;g.timeSlot=__builtin_ctz(f.timeMask);g.bait=preferredChoice(id);
     bool landed=false;
     for(int rig=0;rig<3 && !landed;++rig){
       g.rig=Technique(rig);if(!g.baitWeight(id))continue;
       for(uint32_t seed=0;seed<500000;++seed){
         if((waterHash(seed^0x9d2c5680u)&0x3fff)!=0)continue;
         g.seed=seed;landed=g.drawFish()==id;if(landed)break;
       }
     }
     assert(landed);
   }
 }
 assert(fishCount==originalSpecies || mythics==5);
 for(int choice=0;choice<12;++choice)for(int rig=0;rig<3;++rig)assert(!baitWeightFor(prawn,choice,rig));
 Game drift;drift.emptyCast=true;drift.enter(Phase::Waiting);drift.waitMs=1200;
 drift.tick(600,false,true,1);assert(drift.phase==Phase::Waiting && !drift.teasing());
 drift.tick(600,false,true,1);assert(drift.phase==Phase::Lost && drift.reason==Reason::NoBite && !drift.fileCatch());
 assert(!drift.progress.book.discovered());
 for(int id:{prawn,ray}){Game x;x.fish=id;x.enter(Phase::Bite);x.tick(id==prawn?821:1151,false,true,0);assert(x.reason==Reason::Late);
  x.enter(Phase::Bite);x.tick(300,false,true,0);x.target=x.line=14;
  for(int n=0;n<4000&&x.phase==Phase::Fight;n++)x.tick(16,false,false,x.surge()?0.f:.02f);
  assert(x.phase==Phase::Landed);
 }
 Game g;auto& p=g.progress;
 assert(p.points()==0 && !p.upgrade(0));
 auto catchFish=[&](int id,int length){
   g.fish=id;g.enter(Phase::Fight);
   if(g.surge())g.age=g.runMs+10; // Journal fixture lands the catch in its recovery window.
   g.length=length;g.line=.01f;g.target=6;g.tick(16,false,false,.1f);assert(g.phase==Phase::Landed);
   const auto prior=p.book.entries[id].count;
   g.tick(15000,true,true,1);assert(g.phase==Phase::Landed && p.book.entries[id].count==prior);
   assert(g.fileCatch() && !g.fileCatch());assert(p.book.entries[id].count==prior+1);
 };
 catchFish(0,21);assert(g.pointsAwarded==1 && p.book.discovered()==1 && p.chapter()==1);
 catchFish(0,16);assert(!g.newEntry && !g.personalBest && p.book.entries[0].count==2 && p.book.entries[0].best==21);
 assert(p.upgrade(0)&&p.points()==0&&!p.upgrade(0));
 g.enter(Phase::Bite);g.tick(1530,false,true,0);assert(g.phase==Phase::Fight);
 p.retrain();assert(p.points()==1&&p.upgrade(1));g.line=3;g.heat=0;g.tick(0,false,false,.5f);assert(std::abs(g.line-2.44f)<.001);
 p.retrain();assert(p.upgrade(2));g.heat=0;g.tick(0,false,false,.5f);assert(std::abs(g.heat-.09f)<.001);
 for(int i=1;i<originalSpecies;i++)catchFish(i,catalog[i].low);
 assert(p.book.discovered()==originalSpecies && p.waters()==5 && p.chapter()==5 && p.points()==17);
 p.retrain();assert(p.points()==18);assert(p.upgrade(0)&&p.upgrade(0)&&p.upgrade(0)&&!p.upgrade(0));
 Progress loaded;memcpy(&loaded,&p,sizeof(p));assert(loaded.points()==12&&loaded.book.entries[0].count==2);
 RumblePlan plan;g.fish=0;g.enter(Phase::Waiting);g.waitMs=3500;g.age=2550;
 assert(plan.tick(g,2500,true)==Pulse::Tease && plan.tick(g,2520,true)==Pulse::None);
 g.enter(Phase::Bite);assert(plan.tick(g,3300,true)==Pulse::Bite && plan.tick(g,3320,true)==Pulse::None);
 g.enter(Phase::Fight);g.heat=.98;assert(plan.tick(g,5330,true)==Pulse::Pull);
 assert(plan.tick(g,8000,false)==Pulse::None);
 puts("PASS 250000 weighted casts in 20 habitat/time combinations, original 52 reachable, exclusive Mythic gates, species bait preferences, special hook windows and successful ray/prawn fights, record book, chapter gates, point accounting, three effective upgrades, refund, persistence layout and distinct tease/bite/pull events.");
}
