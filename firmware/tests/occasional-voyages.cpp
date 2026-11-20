#include "Ambient.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <set>
using namespace scenery;
namespace {
constexpr uint32_t tick=64, day=86400000;
bool same(Voyage a,Voyage b){return a.visible==b.visible&&a.x==b.x&&a.y==b.y&&a.dir==b.dir;}
Voyage oldPassive(const Layout& s,uint32_t ms,unsigned live=0){
 const auto t=(ms>>6)+(s.seed&511);
 const unsigned cycle=2048, run=t/cycle, progress=t&(cycle-1), passage=1488;
 if(progress>=passage)return {};
 const int period=live?periodAtUtc((live-1+day-progress*64-(ms&63))%day):s.period;
 if(period==3&&s.place!=1)return {};
 const int dir=(((s.seed>>11)^(s.recipe.feature==Paper?0:run))&1)?-1:1;
 const int x=-42+int(324*progress/passage);
 return {true,dir>0?x:width-1-x,s.horizon+28+int((s.seed>>3)&3)+(triangle(t+(s.seed>>18),16)>12),dir};
}
}
int main(){
 const Layout powered{0xc7a8dc81u,25,1,60,100,{Wide,Boat}};
 constexpr unsigned window=60000;
 unsigned duty=0;for(unsigned k=0;k<window;++k)duty+=voyage(powered,k*tick).visible;assert(duty<window/4);
 unsigned active=0, runs=0, lastEnd=0,dir=0,minGap=window;
 std::set<unsigned> departures;
 for(unsigned k=0;k<window;++k){
  const auto now=voyage(powered,k*tick), prior=voyage(powered,(k-1)*tick);
  assert(same(now,voyage(powered,k*tick)));
  if(now.visible)++active;
  if(now.visible&&!prior.visible){
   ++runs;
   if(runs>1)minGap=minOf(minGap,k-lastEnd);
   departures.insert(k&4095);
   assert(now.x<0||now.x>=width);
   if(dir)assert(unsigned(now.dir)==dir);else dir=unsigned(now.dir);
  }
  if(now.visible&&prior.visible){
   assert(now.dir==prior.dir&&now.dir*(now.x-prior.x)>=0);
  }
  if(!now.visible&&prior.visible&&runs){
   lastEnd=k;
   assert(prior.x<0||prior.x>=width);
  }
 }
 assert(active<window/4); // A visible vessel most of the time is not occasional.
 assert(runs>=12&&runs<=16);
 assert(minGap>1800&&departures.size()>8);
 Layout n=powered;n.period=3;n.place=25;
 unsigned night=0;
 for(unsigned k=0;k<window;++k)night+=voyage(n,k*tick).visible;
 assert(night>0&&night<active/2);
 for(auto f:{Paper,Basket})for(int p=0;p<4;++p)for(unsigned k=0;k<5000;k+=11){
  Layout s=powered;s.recipe.feature=f;s.period=p;
  const unsigned ms=k*tick+21;
  assert(same(voyage(s,ms),oldPassive(s,ms)));
  const unsigned live=(ms+17*3600000)%day+1;
  assert(same(voyage(s,ms,live),oldPassive(s,ms,live)));
 }
 // Any in-flight vessel straddling uint32_t milliseconds rollover must continue.
 bool foundWrap=false,foundBangkok=false;
 for(unsigned seed=1;seed<8192;++seed){
  Layout s=powered;s.seed=seed;
  auto a=voyage(s,UINT32_MAX-39),b=voyage(s,24);
  if(a.visible&&b.visible){
   assert(a.dir==b.dir&&a.dir*(b.x-a.x)>=0&&abs(b.x-a.x)<3);foundWrap=true;
  }
  for(unsigned phase=4096;seed<2&&phase<22000;++phase){
   const uint32_t ms=phase*tick;
   a=voyage(s,ms-1,13*3600000);s.period=3;
   b=voyage(s,ms,13*3600000+1);s.period=1;
   if(a.visible&&b.visible){assert(a.dir==b.dir&&abs(b.x-a.x)<3);foundBangkok=true;}
  }
 }
 assert(foundWrap&&foundBangkok);
 std::printf("visible %.1f%%, daytime runs %u, night %.1f%%, minimum quiet interval %.1fs; passive and boundaries exact\n",100.0*active/window,runs,100.0*night/window,minGap*tick/1000.);
}
