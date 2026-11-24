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
  // Exact reported Chonburi shark, versus a smaller specimen of the same species.
  constexpr int shark=955;
  auto sharkFight=[](int cm){
    Game g;
    g.fish=955;g.length=cm;g.destination=99;g.heat=.16f;
    g.recoverMs=2000;g.runMs=1500;g.slackMs=950;
    g.target=g.line=4.f+std::min(9.f,cm*.065f);
    g.enter(Phase::Fight);
    return g;
  };
  auto giant=sharkFight(145), smallShark=sharkFight(110);
  auto borderline=sharkFight(130);
  assert(borderline.fightStyle()==FightStyle::Heavy && !trophySize(shark,130));
  assert(giant.surge() && giant.rodLoad()>.72f);
  assert(!smallShark.surge() && smallShark.rodLoad()<.40f);
  assert(giant.target>smallShark.target+3.f);
  const float start=giant.line;
  giant.tick(600,false,false,0);
  assert(giant.line>start+.28f && std::abs(giant.pullOffset())>13.f);
  auto reckless=sharkFight(145);
  const auto original=reckless.progress.points();
  for(int i=0;i<20&&reckless.running();++i)reckless.tick(100,false,false,.23f);
  assert(reckless.reason==Reason::Snapped && reckless.progress.points()==original);
  // Find seed selected through the normal cast path once and pin it here.
  Game steady;
  steady.beginSession(1515);steady.arriveAt(99);steady.site=destinations[99].pool;
  steady.timeSlot=2;steady.setBait(preferredChoice(shark));
  steady.tick(16,true,false,0);
  assert(steady.phase==Phase::Flight && steady.fish==shark && steady.length==145);
  steady.tick(castDurationMs,false,false,0);
  assert(steady.phase==Phase::Waiting);
  steady.tick(steady.waitMs+5,false,false,0);
  assert(steady.phase==Phase::Bite);
  steady.tick(20,false,true,0);
  assert(steady.phase==Phase::Fight && steady.surge());
  const auto fightStart=steady;
  int elapsed=0, runs=0;float forward=0;bool wasRun=false,warned=false,tired=false;
  while(steady.running() && elapsed<80000){
    const bool run=steady.surge();runs+=run&&!wasRun;wasRun=run;
    const bool warning=steady.heavyRunSoon();warned|=warning;tired|=steady.heavyTired();
    const float step=(run||warning)?0.f:.04f;forward+=step;
    steady.tick(20,false,false,step);elapsed+=20;
  }
  assert(elapsed>=20000 && elapsed<=35000 && runs>=3 && forward>=18 && forward<=32);
  assert(steady.phase==Phase::Landed && warned && tired);
  assert(steady.landedGrams==42406);
  for(int rank:{0,3})for(bool taps:{false,true}){
    auto paced=fightStart, rushed=fightStart;
    paced.progress.rank[1]=paced.progress.rank[2]=rank;
    rushed.progress.rank[1]=rushed.progress.rank[2]=rank;
    float wound=0;bool warning=false,fatigue=false;
    int i=0;
    for(;i<3000 && paced.running();++i){
      const bool warn=paced.heavyRunSoon();
      warning|=warn;fatigue|=paced.heavyTired();
      const float step=(paced.surge()||warn)?0.f:taps?(i%13==0?.25f:0.f):.02f;
      wound+=step;paced.tick(20,false,false,step);
    }
    assert(paced.phase==Phase::Landed && wound>12.f && wound<35.f && warning && fatigue && i<3000);
    printf("Paced %s rank %d: %d ms, %.2f input turns.\n",taps?"tap":"hold",rank,i*20,wound);
    const auto rushPoints=rushed.progress.points();
    for(int j=0;j<500 && rushed.running();++j)rushed.tick(20,false,false,taps?(j%13==0?.25f:0.f):.02f);
    assert(rushed.phase==Phase::Lost && rushed.reason==Reason::Snapped && rushed.progress.points()==rushPoints);
  }
  auto next=sharkFight(145);next.heavyBestLine=0;assert(next.heavyTired());
  next.enter(Phase::Ready);next.line=next.target=10;next.enter(Phase::Fight);
  assert(next.heavyFight && !next.heavyTired());
  printf("Heavy shark fixture: %d ms, %d runs, %.2f input turns, %d g.\n",elapsed,runs,forward,steady.landedGrams);
  assert(steady.progress.points()==0 && steady.landingReward()==LandingReward::TacklePoint);
  assert(steady.fileCatch() && steady.pointsAwarded==2 && steady.progress.points()==2);
  assert(!steady.fileCatch() && steady.progress.points()==2);
  steady.length=150;steady.enter(Phase::Landed);steady.filed=false;
  assert(steady.landingReward()==LandingReward::PersonalBest);
  assert(steady.fileCatch() && steady.pointsAwarded==0 && steady.progress.points()==2);
  Game saved; saved.progress=steady.progress;
  assert(saved.progress.points()==2);
  saved.progress.rank[0]=1;
  assert(saved.progress.points()==1);
  puts("PASS reported heavy shark run, controls, clean landing, exact weight and one career trophy point.");
  puts("PASS prawn triple picks and paired fight tugs; ray anchoring, interrupted wind and steady-lift release; fast pelagic run, lateral pull and snap under load.");
}
