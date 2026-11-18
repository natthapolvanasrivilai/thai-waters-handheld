#include "../WillowCreek/Creek.h"
#include <cassert>
#include <cstdio>
using namespace creek;

static Game fight(int id) {
  Game g;
  g.fish=id;
  g.line=g.target=10;
  g.enter(Phase::Fight);
  return g;
}

static int countPicks(Game game) {
  game.enter(Phase::Waiting);
  game.waitMs=3400;
  int count=0;
  bool previous=false;
  for(game.age=0;game.age<game.waitMs;game.age+=20){
    const bool active=game.teasing();
    if(active && !previous)++count;
    previous=active;
  }
  return count;
}

int main() {
  Game picker=fight(prawn), anchor=fight(ray), sprinter=fight(47);
  assert(countPicks(picker)==3);
  picker.age=picker.recoverMs+30;
  assert(picker.surge() && picker.rodLoad()<.4f && std::abs(picker.pullOffset())<=5);
  picker.age=picker.recoverMs+picker.runMs/3;
  assert(!picker.surge());
  picker.age=picker.recoverMs+picker.runMs/2;
  assert(picker.surge());

  assert(anchor.holdingBottom() && anchor.rodLoad()>.8f);
  anchor.tick(100,false,false,.25f);
  assert(anchor.line==10 && anchor.pullOffset()==0 && anchor.heat>.3f);
  anchor.rodHeldHigh=true;
  for(int i=0;i<23;i++)anchor.tick(20,false,false,0);
  assert(anchor.holdingBottom());
  anchor.tick(20,false,false,0);
  assert(!anchor.holdingBottom() && anchor.rodLoad()<.6f);
  anchor.tick(20,false,false,.20f);
  assert(anchor.line<9.81f);
  // A new hold needs a fresh steady interval. Winding interrupts the lift.
  anchor.age=anchor.runMs+anchor.recoverMs+anchor.slackMs;
  assert(anchor.holdingBottom());
  for(int i=0;i<16;i++)anchor.tick(20,false,false,0);
  anchor.tick(20,false,false,.05f);
  for(int i=0;i<12;i++)anchor.tick(20,false,false,0);
  assert(anchor.holdingBottom());
  Game patient=fight(ray);
  patient.tick(patient.runMs+1,false,false,0);
  assert(!patient.holdingBottom() && patient.line==10);

  assert(sprinter.surge() && !sprinter.holdingBottom());
  sprinter.tick(600,false,false,0);
  assert(sprinter.line>10.60f && std::abs(sprinter.pullOffset())>17);
  assert(sprinter.rodLoad()>.48f);
  for(int i=0;i<6 && sprinter.running();i++)sprinter.tick(100,false,false,.25f);
  assert(sprinter.reason==Reason::Snapped);
  for(int id=47;id<=51;id++)assert(fight(id).fightStyle()==FightStyle::Sprinter);
  assert(fight(44).fightStyle()==FightStyle::Standard);
  puts("PASS prawn triple picks and paired fight tugs; ray anchoring, interrupted wind and steady-lift release; fast pelagic run, lateral pull and snap under load.");
}
