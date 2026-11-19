#include "../WillowCreek/Rumble.h"
#include "../WillowCreek/Destinations.h"
#include <cassert>
#include <cmath>
#include <cstdio>

using namespace creek;

static Game atZone(unsigned seed,int kind,int place=0,int period=0){
  Game g;
  g.seed=seed;g.destination=place;g.site=destinations[place].pool;g.timeSlot=period;
  const auto z=g.castZone(kind);g.setAim(z.x,z.y);
  g.tick(16,true,false,0);
  assert(g.phase==Phase::Flight);
  g.setAim(.5f,.58f);
  assert(g.aimX==z.x && g.aimY==z.y);
  g.tick(650,false,false,0);
  return g;
}
int main(){
  static_assert(int(Phase::Landed)==5 && int(Phase::Lost)==6 && int(Phase::JunkLanded)==9);
  for(int p=0;p<destinationCount;p++)for(int t=0;t<4;t++){
    Game g;g.destination=p;g.site=destinations[p].pool;g.timeSlot=t;
    assert(g.featureAt(g.aimX,g.aimY)==ClearWater);
    for(int k=Branch;k<=Debris;k++){
      auto zone=g.castZone(k);
      assert(g.featureAt(zone.x,zone.y)==k);
      assert(g.featureAt(zone.x+zone.rx*1.01f,zone.y)!=k);
      assert(zone.x-zone.rx>.04f && zone.x+zone.rx<.96f);
      assert(zone.y-zone.ry>.52f && zone.y+zone.ry<.90f);
    }
  }
  for(unsigned s=1;s<=300;s++)assert(atZone(s,ClearWater).phase==Phase::Waiting);
  auto branch=atZone(5,Branch);
  RumblePlan motor;assert(motor.tick(branch,0,true)==Pulse::Bottom);
  assert(motor.tick(branch,250,true)==Pulse::None);
  branch.tick(200,false,true,0);assert(branch.phase==Phase::Snag);
  branch.tick(300,false,false,0);assert(branch.releaseProgress()==1);
  branch.tick(20,false,false,.08f);assert(branch.releaseProgress()==0);
  branch.tick(500,false,false,0);branch.tick(10,false,true,0);
  assert(branch.phase==Phase::Waiting && branch.contact==0);
  assert(motor.tick(branch,820,true)==Pulse::Tease);
  assert(motor.tick(branch,830,true)==Pulse::None);
  auto rock=atZone(6,Rock,3,2);assert(rock.contact==Rock);
  rock.rodHeldHigh=true;rock.tick(400,false,false,-1.f);assert(rock.releaseProgress()==0);
  rock.rodHeldHigh=false;rock.tick(400,false,false,-.15f);
  assert(rock.phase==Phase::Snag && std::abs(rock.releaseProgress()-.5f)<.001f);
  rock.tick(400,false,false,-.15f);assert(rock.phase==Phase::Waiting);
  auto broken=atZone(6,Rock);
  broken.tick(500,false,false,1.f);assert(broken.phase==Phase::Lost && broken.reason==Reason::Snapped);
  auto cancel=atZone(1,Branch);cancel.abandonCast();
  assert(cancel.phase==Phase::Ready && cancel.contact==0 && cancel.junkId==-1);
  bool found[4]={};int misses=0;
  for(unsigned s=1;s<=150;s++){
    auto g=atZone(s,Debris);if(g.phase==Phase::Waiting){misses++;continue;}
    assert(g.phase==Phase::HaulingJunk && g.junkId>=0 && g.junkId<4);
    found[g.junkId]=true;RumblePlan haptic;assert(haptic.tick(g,0,true)==Pulse::Pull);
    g.tick(500,false,false,-.3f);assert(g.releaseProgress()==0);
    g.tick(500,false,false,.5f);assert(g.releaseProgress()>0 && g.releaseProgress()<1);
    g.tick(1500,false,false,1.5f);assert(g.phase==Phase::JunkLanded);
    assert(haptic.tick(g,2000,true)==Pulse::Tease && haptic.tick(g,2010,true)==Pulse::None);
    assert(g.progress.book.discovered()==0 && g.pointsAwarded==0 && g.catches==0);
    assert(!g.running() && g.releaseProgress()==1);
    g.setAim(.5f,.67f);g.tick(16,true,false,0);assert(g.phase==Phase::Flight && g.junkId==-1);
  }
  assert(misses>0 && found[0] && found[1] && found[2] && found[3]);
  printf("PASS %d water/period combinations, all 4 salvage items, release/overwind/abandon, protected center, one-shot rumble and no fish credit.\n",4*destinationCount);
}
