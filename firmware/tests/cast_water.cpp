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
  g.tick(creek::castDurationMs,false,false,0);
  return g;
}
int main(){
  static_assert(int(Phase::Landed)==5 && int(Phase::Lost)==6 && int(Phase::JunkLanded)==9);
  for(int p=0;p<destinationCount;p++)for(int t=0;t<4;t++){
    Game g;g.destination=p;g.site=destinations[p].pool;g.timeSlot=t;
    assert(g.featureAt(g.aimX,g.aimY)==ClearWater);
    bool emptySeen=false,occupiedSeen=false;
    for(g.seed=1;g.seed<=40;g.seed++){
    bool occupied=false;
    for(int k=Branch;k<=Debris;k++){
      auto zone=g.castZone(k);
      bool present=hasWaterFeature(g.waterLayout(),p,g.site,k);
      assert(g.featureAt(zone.x,zone.y)==(present?k:ClearWater));
      occupied|=present;
      assert(g.featureAt(zone.x+zone.rx*1.01f,zone.y)!=k);
      assert(zone.x-zone.rx>.04f && zone.x+zone.rx<.96f);
      assert(zone.y-zone.ry>.52f && zone.y+zone.ry<.90f);
    }
    emptySeen|=!occupied;occupiedSeen|=occupied;
    }
    assert(emptySeen && occupiedSeen);
  }
  assert(hazardOdds(106,4,Branch)==0 && hazardOdds(106,4,Rock)==0);
  assert(hazardOdds(34,0,Rock)==0 && hazardOdds(7,3,Rock)>50);
  for(unsigned s=1;s<=300;s++)assert(atZone(s,ClearWater).phase==Phase::Waiting);
  for(const auto kind:{Branch,Rock}){
    auto repeated=atZone(kind==Branch?2:5,kind);
    assert(repeated.phase==Phase::Snag);
    const auto spot=repeated.castZone(kind);const auto original=repeated.waterLayout();
    for(int i=0;i<6;i++){
      repeated.abandonCast();
      repeated.timeSlot=i%4;
      repeated.setAim(spot.x,spot.y);repeated.tick(16,true,false,0);repeated.tick(creek::castDurationMs,false,false,0);
      assert(repeated.phase==Phase::Snag && repeated.contact==kind && repeated.waterLayout()==original);
    }
    repeated.abandonCast();repeated.setAim(.5f,.67f);
    repeated.tick(16,true,false,0);repeated.tick(creek::castDurationMs,false,false,0);
    assert(repeated.phase==Phase::Waiting);
    repeated.lose(Reason::Early);repeated.updateWeather(8,20211);
    assert(repeated.waterLayout()!=original);
    repeated.updateWeather(1,20300);assert(repeated.waterLayout()==original);
    repeated.arriveAt(16);repeated.arriveAt(0);assert(repeated.waterLayout()!=original);
  }
  puts("PASS persistent branch and rock across repeated casts and light changes, avoidance, new season and return visits.");
  auto branch=atZone(2,Branch);
  RumblePlan motor;assert(motor.tick(branch,0,true)==Pulse::Bottom);
  assert(motor.tick(branch,250,true)==Pulse::None);
  branch.tick(200,false,true,0);assert(branch.phase==Phase::Snag);
  branch.tick(300,false,false,0);assert(branch.releaseProgress()==1);
  branch.tick(20,false,false,.08f);assert(branch.releaseProgress()==0);
  branch.tick(500,false,false,0);branch.tick(10,false,true,0);
  assert(branch.phase==Phase::Waiting && branch.contact==0);
  assert(motor.tick(branch,820,true)==Pulse::Tease);
  assert(motor.tick(branch,830,true)==Pulse::None);
  auto rock=atZone(1,Rock,3,2);assert(rock.contact==Rock);
  rock.rodHeldHigh=true;rock.tick(400,false,false,-1.f);assert(rock.releaseProgress()==0);
  rock.rodHeldHigh=false;rock.tick(400,false,false,-.15f);
  assert(rock.phase==Phase::Snag && std::abs(rock.releaseProgress()-.5f)<.001f);
  rock.tick(400,false,false,-.15f);assert(rock.phase==Phase::Waiting);
  auto broken=atZone(5,Rock);
  broken.tick(500,false,false,1.f);assert(broken.phase==Phase::Lost && broken.reason==Reason::Snapped);
  auto cancel=atZone(2,Branch);cancel.abandonCast();
  assert(cancel.phase==Phase::Ready && cancel.contact==0 && cancel.junkId==-1);
  bool found[salvage::count]={};int misses=0;
  for(int place=0;place<destinationCount;place++)for(unsigned s=1;s<=150;s++){
    auto g=atZone(s,Debris,place);if(g.phase==Phase::Waiting){misses++;continue;}
    assert(g.phase==Phase::HaulingJunk && g.junkId>=0 && g.junkId<salvage::count);
    assert(salvage::items[g.junkId].habitats & recoveryHabitats(place,g.site));
    found[g.junkId]=true;RumblePlan haptic;assert(haptic.tick(g,0,true)==Pulse::Pull);
    g.tick(500,false,false,-.3f);assert(g.releaseProgress()==0);
    g.tick(500,false,false,.5f);assert(g.releaseProgress()>0 && g.releaseProgress()<1);
    g.tick(1500,false,false,1.5f);assert(g.phase==Phase::JunkLanded);
    assert(haptic.tick(g,2000,true)==Pulse::Tease && haptic.tick(g,2010,true)==Pulse::None);
    assert(g.progress.book.discovered()==0 && g.pointsAwarded==0 && g.catches==0);
    assert(!g.running() && g.releaseProgress()==1);
    g.setAim(.5f,.67f);g.tick(16,true,false,0);assert(g.phase==Phase::Flight && g.junkId==-1);
  }
  assert(misses>0);for(bool recovered:found)assert(recovered);
  assert(rainChance(113,7,1)>rainChance(113,1,1));
  assert(rainChance(108,11,2)>rainChance(0,11,2));
  assert(rainChance(0,8,2)>rainChance(0,8,0));
  assert(rainChance(96,6,1)>rainChance(0,6,1));
  bool forecast[4]={};for(unsigned day=0;day<600;day++)
    forecast[int(seasonalWeather(113,8,day,2))]=true;
  for(bool observed:forecast)assert(observed);
  Game weatherGame[4];
  for(int level=0;level<4;level++){
    auto& g=weatherGame[level];g.weatherMode=level+1;g.updateWeather(7,20111);
    assert(int(g.weather)==level);g.tick(16,true,false,0);
    g.weatherMode=1;g.updateWeather(1,21876);assert(int(g.weather)==level);
    WeatherStroke frame[maxWeatherStrokes];
    int a=weatherStrokes(frame,g.weather,0,0,1);
    auto old=frame[0];int b=weatherStrokes(frame,g.weather,220,0,1);
    assert(a>=0 && b>=0 && a<=maxWeatherStrokes && b<=maxWeatherStrokes);
    if(level)assert(old.x!=frame[0].x || old.y!=frame[0].y);
  }
  assert(weatherGame[1].waitMs<weatherGame[0].waitMs);
  assert(weatherGame[2].waitMs>weatherGame[0].waitMs && weatherGame[3].waitMs>weatherGame[2].waitMs);
  puts("PASS regional monsoons, dusk rain weights, four animated conditions, cast lock and bite timing.");
  printf("PASS %d water/period combinations, all 12 habitat-matched salvage items, release/overwind/abandon, protected center, one-shot rumble and no fish credit.\n",4*destinationCount);
}
