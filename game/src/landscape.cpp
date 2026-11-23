#include "../../firmware/WillowCreek/Ambient.h"
#include "../../firmware/WillowCreek/BoatAmbience.h"
#include "../../firmware/WillowCreek/ArrivalPixels.h"

namespace {
uint8_t indexed[scenery::width*scenery::height];
scenery::Color palette[scenery::colorCount];
scenery::Layout layout{};
struct Span {uint8_t x,y,length,ink;};
constexpr int capacity=256;
Span spans[capacity];
uint16_t boatMix;
scenery::BoatAmbience boatVoice;
int16_t boatSamples[256];
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
namespace {arrival::Frame arrivalFrame;uint8_t arrivalLayer[scenery::width*scenery::height];}
extern "C" {
int arrivalDuration(){return arrival::duration;}
int arrivalLanding(int place,int pool){return arrival::landing(place,pool);}
int16_t* arrivalShapes(){return reinterpret_cast<int16_t*>(arrivalFrame.shapes);}
int sampleArrival(int place,int pool,unsigned ms){
  arrival::draw(arrivalFrame,place,pool,ms);
  return arrivalFrame.count;
}
uint8_t* arrivalPixels(int place,int pool,unsigned ms){
  arrival::draw(arrivalFrame,place,pool,ms);
  for(auto& value:arrivalLayer)value=255;
  arrival::raster(arrivalFrame,[](int x,int y,uint8_t ink){arrivalLayer[y*scenery::width+x]=ink;});
  return arrivalLayer;
}
uint8_t* paintPlace(int place,int period){
  scenery::render({indexed},palette,place,period,&layout);
  return indexed;
}
uint32_t* placePalette(){return palette;}
uint8_t* ambientSpans(){return reinterpret_cast<uint8_t*>(spans);}
int sampleAmbient(uint32_t ms,unsigned utcDayPlusOne,int reducedMotion=0){
  WebSpans out;
  scenery::paintAmbient(out,layout,ms,utcDayPlusOne,&boatMix,reducedMotion!=0);
  return out.count<=capacity?out.count:-1;
}
#if defined(__wasm__)
__attribute__((export_name("ambientBoatMix")))
#endif
unsigned ambientBoatMix(){return boatMix;}
#if defined(__wasm__)
__attribute__((export_name("ambientBoatPcm")))
#endif
const int16_t* ambientBoatPcm(unsigned mix,unsigned volume){
  for(auto& v:boatSamples)v=boatVoice.sample(uint16_t(mix),volume);
  return boatSamples;
}
}
