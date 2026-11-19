#pragma once
#include <cstdint>
#include <cmath>
#include <algorithm>

namespace creek {
enum WaterFeature { ClearWater=0, Branch=1, Rock=2, Debris=3 };
struct CastZone {
  float x,y,rx,ry;
  float distanceSquared(float u,float v) const {
    float dx=(u-x)/rx,dy=(v-y)/ry;
    return dx*dx+dy*dy;
  }
};
// The atlas uses normalized coordinates in the whole landscape LCD, Y down.
// A protected middle lane gives a new player a predictable first cast.
inline uint32_t waterHash(uint32_t value){
  value^=value>>16;value*=0x7feb352du;value^=value>>15;
  value*=0x846ca68bu;return value^(value>>16);
}
inline CastZone waterZone(int place,int pool,int period,int kind){
  if(kind<Branch||kind>Debris)return {.50f,.67f,.075f,.11f};
  const uint32_t shore=waterHash(uint32_t(place+1)*31u+uint32_t(pool));
  const uint32_t feature=waterHash(shore+uint32_t(kind)*71u);
  const bool mirror=(shore&1u)!=0;
  // Persistent structure stays on the same bank all day. Changing waterlight
  // and current alter the effective opening or the debris eddy a little.
  const float sway=(period-1.5f)*.009f;
  const float variation=float((feature>>8)%41)*.001f;
  float x,y,rx,ry;
  if(kind==Branch){
    x=.16f+variation+(pool==4?.033f:0);
    y=.605f+float((feature>>16)%60)*.001f+sway*.4f;
    rx=pool==1||pool==3?.100f:.081f;ry=.043f;
  }else if(kind==Rock){
    x=.78f+variation;y=.70f+float((feature>>16)%70)*.001f+sway*.5f;
    rx=pool==2||pool==4?.104f:.079f;ry=.049f;
  }else{
    x=.292f+variation+sway;
    y=.795f+float((feature>>16)%32)*.001f+sway*.45f;
    rx=pool==4?.091f:.079f;ry=.046f;
  }
  return {mirror?1-x:x,y,rx,ry};
}
}
