#pragma once
#include "ScenicRecipes.h"
#include <cstdint>

namespace creek {
enum WaterFeature { ClearWater=0, Branch=1, Rock=2, Debris=3 };
struct CastZone {
  float x,y,rx,ry;
  float distanceSquared(float u,float v) const {
    float dx=(u-x)/rx,dy=(v-y)/ry;
    return dx*dx+dy*dy;
  }
};
inline uint32_t waterHash(uint32_t value){
  value^=value>>16;value*=0x7feb352du;value^=value>>15;
  value*=0x846ca68bu;return value^(value>>16);
}
// Per-visit occurrence rates use the terrain already drawn for this destination.
// Exposed sea has no submerged trees. Estuaries can carry driftwood.
inline int hazardOdds(int place,int pool,int kind){
  using namespace scenery;
  const Recipe habitat=recipes[place];
  if(kind==creek::Branch){
    if(pool==4)return habitat.water==Estuary?18:0;
    if(habitat.water==Marsh || habitat.feature==Roots || habitat.feature==Snag)return 63;
    return habitat.water==scenery::Stream || habitat.water==Bend?48:30;
  }
  if(kind==creek::Rock){
    if(habitat.water==Marsh || habitat.water==Gulf)return 0;
    if(habitat.water==Gorge || habitat.water==Karst || habitat.water==Headland ||
       habitat.water==scenery::Stream || habitat.feature==Rocks)return 70;
    return habitat.water==Island || habitat.water==Foothill?48:22;
  }
  if(kind==creek::Debris)return habitat.feature==Nets || habitat.feature==Pier ||
    habitat.feature==Ferry || habitat.feature==Market?48:20;
  return 0;
}
// Coordinates are normalized to the whole LCD. Disjoint depth bands keep
// overlapping structures from masking each other, with room to fish midstream.
inline CastZone waterZone(uint32_t layout,int kind){
  if(kind<Branch||kind>Debris)return {.50f,.67f,.075f,.11f};
  uint32_t shape=waterHash(layout+uint32_t(kind)*71u);
  float x=.165f+float((shape>>8)%175)*.001f;
  if(shape&1u)x=1-x;
  float y=(kind==Branch?.594f:kind==Rock?.697f:.806f)+float((shape>>18)%22)*.001f;
  return {x,y,.071f+float((shape>>24)%20)*.001f,.040f};
}
inline bool hasWaterFeature(uint32_t layout,int place,int pool,int kind){
  return int(waterHash(layout^uint32_t(kind)*0x85ebca6bu)%100)<hazardOdds(place,pool,kind);
}
}
