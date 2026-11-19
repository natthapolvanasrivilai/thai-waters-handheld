#include "../../firmware/WillowCreek/Ambient.h"

namespace {
uint8_t indexed[scenery::width*scenery::height];
scenery::Color palette[scenery::colorCount];
scenery::Layout layout{};
struct Span {uint8_t x,y,length,ink;};
constexpr int capacity=256;
Span spans[capacity];
struct WebSpans {
  int count=0;
  void span(int x,int y,int n,int ink){
    int stop=scenery::minOf(scenery::width,x+n);
    x=scenery::maxOf(0,x);
    if(unsigned(y)>=scenery::height||stop<=x)return;
    if(count<capacity)spans[count]={uint8_t(x),uint8_t(y),uint8_t(stop-x),uint8_t(ink)};
    ++count;
  }
  int base(int x,int y)const{return indexed[x*scenery::height+scenery::height-1-y];}
  bool water(int x,int y)const{return scenery::waterInk(base(x,y));}
  bool sky(int x,int y)const{int c=base(x,y);return c<=scenery::Glow||c>=scenery::Star;}
  bool foliage(int x,int y)const{int c=base(x,y);return c==scenery::Leaf||c==scenery::Reed||c==scenery::Tip;}
};
}
extern "C" {
uint8_t* paintPlace(int place,int period){
  scenery::render({indexed},palette,place,period,&layout);
  return indexed;
}
uint32_t* placePalette(){return palette;}
uint8_t* ambientSpans(){return reinterpret_cast<uint8_t*>(spans);}
int sampleAmbient(uint32_t ms,unsigned utcDayPlusOne){
  WebSpans out;
  scenery::paintAmbient(out,layout,ms,utcDayPlusOne);
  return out.count<=capacity?out.count:-1;
}
}
