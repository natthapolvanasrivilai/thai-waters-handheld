#pragma once
#include "Ambient.h"

namespace scenery {
struct LcdSpans {
  uint16_t *frame;
  const uint16_t *base,*lcd;
  static int offset(int x,int y){return 2*x*320+318-2*y;}
  void span(int x,int y,int n,int ink){
    if(unsigned(y)>=scenery::height)return;
    int stop=scenery::minOf(scenery::width,x+n);
    for(x=scenery::maxOf(0,x);x<stop;x++){
      int p=offset(x,y);frame[p]=frame[p+1]=frame[p+320]=frame[p+321]=lcd[ink];
    }
  }
  bool water(int x,int y)const{
    uint16_t c=base[offset(x,y)];
    if(c==lcd[scenery::Deep]||c==lcd[scenery::Wake])return true;
    for(int i=scenery::WaterTop;i<scenery::Far;i++)if(lcd[i]==c)return true;
    return false;
  }
  bool sky(int x,int y)const{
    uint16_t c=base[offset(x,y)];
    for(int i=0;i<=scenery::Glow;i++)if(lcd[i]==c)return true;
    for(int i=scenery::Star;i<57;i++)if(lcd[i]==c)return true;
    return false;
  }
  bool foliage(int x,int y)const{
    uint16_t c=base[offset(x,y)];
    return c==lcd[scenery::Leaf]||c==lcd[scenery::Reed]||c==lcd[scenery::Tip];
  }
};
}
