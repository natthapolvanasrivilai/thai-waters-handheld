#include "../WillowCreek/Creek.h"
#include "../WillowCreek/Destinations.h"
#include <cassert>
#include <cstdio>
using namespace creek;

static void castInto(Game& game){
  game.tick(20,true,false,0);
  game.tick(650,false,false,0);
  assert(game.phase==Phase::Waiting);
}

static void drawStrike(Game& game){
  for(int i=0;i<1100 && game.phase==Phase::Waiting;i++){
    bool lift=game.rig==Technique::Jig && !game.falling;
    float turns=game.rig==Technique::Spoon && !game.falling ? .035f : 0;
    game.tick(20,false,lift,turns);
  }
  assert(game.phase==Phase::Bite);
  game.tick(150,false,true,0);
  assert(game.phase==Phase::Fight);
}

int main(){
  int landed=0,steadyLosses=0;
  for(int place=0;place<destinationCount;place++)for(int slot=0;slot<4;slot++)for(int rig=0;rig<3;rig++){
    Game g;g.seed=unsigned(1+place*163+slot*7+rig);g.destination=place;
    g.site=destinations[place].pool;g.timeSlot=slot;g.setRig(rig);
    assert(g.setBait(preferredChoice(stockId(g.site,0))));
    castInto(g);drawStrike(g);
    Game steady=g;
    for(int t=0;t<6000 && g.phase==Phase::Fight;t++)
      g.tick(20,false,false,g.surge()?0.f:.027f);
    assert(g.phase==Phase::Landed && g.catches==1);++landed;
    for(int t=0;t<6000 && steady.phase==Phase::Fight;t++)
      steady.tick(20,false,false,.020f);
    if(steady.phase==Phase::Lost)++steadyLosses;
  }
  assert(steadyLosses>landed/2);
  for(int rig:{1,2}){
    Game g;g.setRig(rig);castInto(g);
    for(int i=0;i<1250;i++)g.tick(20,false,false,0);
    assert(g.phase==Phase::Lost && g.reason==Reason::Unworked);
  }
  Game jig;jig.setRig(2);castInto(jig);jig.rodHeldHigh=true;
  jig.tick(20,false,true,0);
  for(int i=0;i<75;i++)jig.tick(20,false,false,0);
  assert(jig.strokes==0);
  jig.rodHeldHigh=false;
  for(int i=0;i<40;i++)jig.tick(20,false,false,0);
  assert(jig.strokes==1);
  Game spoon;spoon.setRig(1);castInto(spoon);
  for(int i=0;i<600;i++)spoon.tick(20,false,false,.025f);
  assert(spoon.strokes==0 && spoon.phase==Phase::Waiting);
  std::printf("PASS %d landable spot/time/technique combinations; %d fixed-speed fights lost. Idle lures, continuous spoon retrieve, and held-high jigs cannot draw strikes.\n",landed,steadyLosses);
}
