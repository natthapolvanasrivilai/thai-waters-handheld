#include "../WillowCreek/Rumble.cpp"
#include <cstdio>
#include <cassert>
uint32_t testClock=0;
int main(){
 Wire.nack=true;assert(!initRumble());Wire.nack=false;Wire.id=0x60;assert(!initRumble());assert(Wire.log.empty());
 Wire.id=0xe0;assert(initRumble());auto base=Wire.log.size();driveRumble(Pulse::Pull,0,1);assert(Wire.log.size()==base);
 bool motorClampSet=false;
 for(const auto& reg:Wire.log)if(reg==std::make_pair(0x17,138))motorClampSet=true;
 assert(motorClampSet);
 const int effects[6][3]={{63,62,61},{29,28,27},{51,50,49},{6,5,4},{51,50,49},{36,35,34}};
 for(int p=0;p<6;p++)for(int level=1;level<=3;level++){
  auto n=Wire.log.size();auto pulse=static_cast<Pulse>(p+1);
  assert(driveRumble(pulse,level,.3));
  const int id=effects[p][level-1],tail=pulse==Pulse::Bottom?id:pulse==Pulse::Dash?27-level:0;
  assert(Wire.log[n]==std::make_pair(12,0)&&Wire.log[n+1]==std::make_pair(4,id)&&Wire.log[n+2]==std::make_pair(5,tail));
  if(tail)assert(Wire.log[n+3]==std::make_pair(6,0));
  assert(Wire.log.back()==std::make_pair(12,1));
 }
 using namespace creek;
 for(int id:{prawn,ray,51}){
  RumblePlan plan;Game game;game.fish=id;game.enter(Phase::Fight);
  const Pulse expected=id==prawn?Pulse::Pick:id==ray?Pulse::Bottom:Pulse::Dash;
  unsigned matches=0,runMs=0;
  for(unsigned ms=0;ms<12000;ms+=16){
   game.age=ms;const auto cue=plan.tick(game,ms,true);
   if(game.surge())runMs+=16;
   if(cue==expected){assert(game.surge());++matches;}
  }
  assert(matches>=2 && runMs>0);
  game.enter(Phase::Landed);
  auto end=plan.tick(game,12000,true);
  assert(end==Pulse::None||end==Pulse::Stop);
  assert(plan.tick(game,12016,true)==Pulse::None);
 }
 auto sample=Wire.log.size();
 assert(driveRumble(Pulse::PickSample,1,0));
 assert(Wire.log[sample+1]==std::make_pair(4,6)&&Wire.log[sample+2]==std::make_pair(5,162)&&
        Wire.log[sample+3]==std::make_pair(6,6)&&Wire.log[sample+4]==std::make_pair(7,162)&&
        Wire.log[sample+5]==std::make_pair(8,6)&&Wire.log[sample+6]==std::make_pair(9,0));
 assert(driveRumble(Pulse::Dash,1,.3));assert(driveRumble(Pulse::Stop,1,0));assert(Wire.log.back()==std::make_pair(12,0));
 stopRumble();assert(Wire.log.back()==std::make_pair(12,0));Wire.nack=true;assert(!driveRumble(Pulse::Pull,2,.8f));
 puts("PASS DRV2605L detection, mute, 18 finite ROM motif/strength sequences, species timing, cancellation and I2C failure.");
}
