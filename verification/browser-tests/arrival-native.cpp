#include "../../firmware/WillowCreek/ArrivalPixels.h"
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>

using namespace arrival;
static void near(float actual,float want,float tolerance=.003f){
  if(std::fabs(actual-want)>tolerance){
    std::fprintf(stderr,"arrival: expected %.4f, got %.4f\n",want,actual);
    assert(false);
  }
}
static int pixels(const Frame& f){
  int count=0;
  raster(f,[&](int x,int y,uint8_t k){
    assert(unsigned(x)<scenery::width&&unsigned(y)<scenery::height&&k<scenery::colorCount);
    ++count;
  });
  return count;
}
int main(){
  static_assert(duration==4200&&raiseRod==3330);
  const struct {int site,pool; Route type; float speed,metres;} routes[]={
    {16,0,Footpath,1.20f,3.426f},{4,0,Hike,.95f,2.71225f},
    {3,0,Drive,6.f,17.13f},{2,0,Longtail,3.f,8.565f},
  };
  static Frame f;
  std::array<bool,64> ranks{};
  for(int y=0;y<8;++y)for(int x=0;x<8;++x){
    const unsigned rank=revealRank(x,y);
    assert(rank<ranks.size()&&!ranks[rank]);ranks[rank]=true;
    assert(rank==revealRank(x+8,y+8));
  }
  for(const auto& r:routes){
    assert(landing(r.site,r.pool)==r.type);
    const auto distance=[&](unsigned age){
      draw(f,r.site,r.pool,age);
      return f.distance;
    };
    near(distance(0),0); near(distance(300),r.speed*.150f);
    near(distance(1200)-distance(700),r.speed*.5f);
    near(distance(2680),r.speed*2.530f);
    near(distance(3330),r.metres);
    near(f.center,239);near(f.horizon,128);
    near(f.eye,1.16f);
    near(distance(3760),r.metres);
    float last=0;
    for(unsigned t=0;t<=3760;t+=7){
      const float current=distance(t);
      assert(current>=last&&current<=r.metres+.003f);
      assert(f.count<maxShapes);
      last=current;
    }
    draw(f,r.site,r.pool,2100);const int open=pixels(f);assert(open>500);
    draw(f,r.site,r.pool,3330);assert(pixels(f)>0);
    draw(f,r.site,r.pool,3759);assert(pixels(f)<open/10);
    draw(f,r.site,r.pool,3760);assert(pixels(f)==0);
    draw(f,r.site,r.pool,duration);assert(pixels(f)==0);
  }
  std::puts("PASS native arrival route distances, motion timing and indexed bank reveal");
}
