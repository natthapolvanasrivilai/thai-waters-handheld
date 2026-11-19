#pragma once
#include "CastWater.h"

namespace creek {
enum class Weather : uint8_t { Clear, LightRain, HeavyRain, Storm };
constexpr const char* weatherNames[]={"Clear","Light rain","Heavy rain","Storm"};
constexpr const char* weatherChoices[]={"Seasonal","Clear","Light rain","Heavy rain","Storm"};

// Game probabilities follow the Thai southwest monsoon and the later wet
// season on the southern Gulf coast. They are illustrative, offline weights.
inline int rainChance(int place,int month,int period){
  constexpr uint8_t inland[]={9,11,17,27,54,53,61,69,73,44,18,8};
  constexpr uint8_t east[]={12,17,26,38,66,70,73,76,79,56,24,13};
  constexpr uint8_t southernGulf[]={45,22,21,33,48,40,42,46,53,68,81,72};
  constexpr uint8_t andaman[]={18,15,25,46,73,71,73,78,84,75,51,27};
  const bool gulf=place==2 || place==95 || (place>=105 && place<=110);
  const bool eastern=(place>=90 && place<=92) || (place>=96 && place<=99);
  const auto profile=place>=111?andaman:gulf?southernGulf:eastern?east:inland;
  return profile[month-1]+(period==2?8:period==1?3:period==0?-4:0);
}
inline Weather seasonalWeather(int place,int month,uint32_t day,int period){
  const int chance=rainChance(place,month,period);
  uint32_t roll=waterHash(day*0x85ebca6bu+uint32_t(place)*977u+uint32_t(period)*7u);
  if(int(roll%100)>=chance)return Weather::Clear;
  int intensity=(roll>>10)%100;
  if(intensity<(chance/7+(period==2?4:0)))return Weather::Storm;
  return intensity<20+chance/3?Weather::HeavyRain:Weather::LightRain;
}
inline uint32_t weatherTint(uint32_t color,Weather conditions){
  const int level=int(conditions);
  if(!level)return color;
  // Preserve the time-of-day palette and its contrast under cloud cover.
  const unsigned red=(color>>16&255)*(100-11*level)/100;
  const unsigned green=(color>>8&255)*(100-9*level)/100+2*level;
  const unsigned blue=(color&255)*(100-6*level)/100+4*level;
  return red<<16|green<<8|blue;
}
// Endpoints are in physical 480 x 320 scene coordinates. Both renderers
// consume the exact same moving strokes, water glints and distant lightning.
struct WeatherStroke { int16_t x,y,endX,endY,ink; };
constexpr int maxWeatherStrokes=100;
constexpr uint32_t weatherInk[]={0x9caeb5,0xb3d2d2,0xe2e2bc,0xb8d5bf};
inline int weatherStrokes(WeatherStroke* out,Weather conditions,uint32_t ms,int place,int period){
  int level=int(conditions),count=0;
  const uint32_t frame=ms/32,local=waterHash(uint32_t(place+1)*13u+period);
  auto line=[&](int x,int y,int ex,int ey,int ink){
    out[count++]={int16_t(x),int16_t(y),int16_t(ex),int16_t(ey),int16_t(ink)};
  };
  const int drops=level==1?13:level==2?34:level==3?57:0;
  for(int i=0;i<drops;++i){
    uint32_t h=waterHash(local+uint32_t(i));
    unsigned phase=(frame*uint32_t(4+level*2+(h&1))+(h>>16))%350;
    int x=int(((h&65535)+phase*unsigned(level)/3)%505)-12;
    int y=int(phase)-14;
    line(x,y,x+level*2-1,y+2+level*2,level==1?0:(i%5==0?1:0));
  }
  // Ringlets form at a new position on each impact. Clear water catches
  // only occasional glints, including a subdued moon glint after dark.
  int rings=level?level*3:2;
  for(int i=0;i<rings;++i){
    unsigned age=frame+unsigned(i*13);
    uint32_t h=waterHash(local+uint32_t(i)*707+age/29);
    unsigned phase=age%29;
    if(phase>13)continue;
    int x=32+int(h%416),y=184+int((h>>10)%91),r=1+phase/4;
    int ink=level?1:period==3?0:3;
    line(x-r,y,x-1,y,ink);line(x+1,y,x+r,y,ink);
  }
  if(level==3 && (frame+local%400)%400<5){
    int x=80+int(waterHash(local+frame/400)%320);
    line(x,35,x-9,49,2);line(x-9,49,x-3,49,2);line(x-3,49,x-14,66,2);
  }
  return count;
}
}
