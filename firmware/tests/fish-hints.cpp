#include "../WillowCreek/Creek.h"
#include "../WillowCreek/Destinations.h"
#include <cassert>
#include <cstdio>
using namespace creek;

static Game at(int place,unsigned seed){
  Game g;
  g.beginSession(seed);g.arriveAt(place);
  g.site=destinations[place].pool;g.timeSlot=0;
  return g;
}
int main(){
  Game sample; FishHint active;
  int visible=0,small=0,large=0;
  for(int place=0;place<destinationCount;place++){
    auto g=at(place,817+place);
    const unsigned before=g.seed;
    int lastStart=-100000;bool wasVisible=false;
    g.tick(40000,false,false,0);assert(!g.fishHint().visible());
    for(int t=40000;t<=132000;t+=100){
      g.tick(100,false,false,0);
      auto h=g.fishHint();
      if(!h.visible()){wasVisible=false;continue;}
      if(!wasVisible){assert(t-lastStart>=47500);lastStart=t;wasVisible=true;}
      assert(h.species>=0 && catalog[h.species].tier!=5 && g.drawWeight(h.species)>=2 && livesHere(h.species,place,0));
      assert(h.x>=.12f&&h.x<=.88f&&h.y>=.59f&&h.y<=.82f&&g.featureAt(h.x,h.y)==ClearWater);
      assert(h.phase>=0.f&&h.phase<1.f);
      if(h.large){++large;assert(catalog[h.species].high>=47);}
      else{++small;assert(catalog[h.species].high<47);}
      if(!active.visible()){active=h;sample=g;}
      ++visible;
    }
    assert(g.seed==before);
  }
  assert(visible&&small&&large&&active.visible());

  auto near=sample;
  near.setAim(active.x,active.y);
  assert(near.hintTargetAtAim()==active.species);
  auto far=sample;
  far.setAim(active.x<.5f?.92f:.08f,.86f);
  assert(far.hintTargetAtAim()==-1);
  auto disabled=sample;disabled.setFishHints(false);
  assert(!disabled.fishHint().visible()&&disabled.hintTargetAtAim()==-1);
  auto expired=sample;expired.tick(3000,false,false,0);
  assert(!expired.fishHint().visible()&&expired.hintTargetAtAim()==-1);
  auto otherVisit=sample;otherVisit.arriveAt((sample.destination+1)%destinationCount);
  assert(!otherVisit.fishHint().visible()&&otherVisit.hintTargetAtAim()==-1);
  auto incompatible=sample;incompatible.timeSlot=(incompatible.timeSlot+1)%4;
  assert(!incompatible.fishHint().visible()&&incompatible.hintTargetAtAim()==-1);
  incompatible=sample;incompatible.setBait((sample.bait+1)%baitCount);
  assert(!incompatible.fishHint().visible()&&incompatible.hintTargetAtAim()==-1);

  int nearby=0,baseline=0;
  for(unsigned seed=1;seed<=18000;seed++){
    auto a=near,b=near;
    a.seed=b.seed=seed;b.setFishHints(false);
    a.tick(12,true,false,0);b.tick(12,true,false,0);
    assert(a.seed==b.seed);
    assert(a.phase==Phase::Flight&&b.phase==Phase::Flight);
    assert(!a.fishHint().visible()&&!b.fishHint().visible());
    if(!a.emptyCast&&a.fish==active.species)++nearby;
    if(!b.emptyCast&&b.fish==active.species)++baseline;
    auto c=far,d=far;
    c.seed=d.seed=seed;d.setFishHints(false);
    c.tick(12,true,false,0);d.tick(12,true,false,0);
    assert(c.seed==d.seed&&c.fish==d.fish&&c.length==d.length&&c.emptyCast==d.emptyCast);
  }
  assert(baseline>0 && nearby>baseline && nearby<18000);
  std::printf("PASS %d small/%d large cue frames; actual near casts %d vs %d baseline over 18000; LCG and miss controls exact\n",small,large,nearby,baseline);
}
