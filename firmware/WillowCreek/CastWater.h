#pragma once
#include "ScenicRecipes.h"
#include "SalvageCatalog.h"
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
// These are gameplay habitat associations, drawn from the location artwork.
inline uint16_t recoveryHabitats(int place,int pool){
  using namespace scenery;
  const auto r=recipes[place];
  const bool inland=pool!=4;
  const bool landing=r.feature==Pier||r.feature==Ferry||r.feature==Raft||r.feature==Boathouse||
                     r.feature==Market||r.feature==Boat||r.feature==Nets||r.feature==Kitchen;
  uint16_t tags=salvage::any;
  if(inland)tags|=salvage::bank;
  if(landing)tags|=salvage::landing;
  if(inland&&landing)tags|=salvage::landingInland;
  if(inland&&(r.water==Marsh||r.water==Lake||r.feature==Lotus))tags|=salvage::still;
  if(inland&&(r.water==Bend||r.water==Wide||r.water==scenery::Stream||r.water==Gorge))tags|=salvage::flow;
  if(inland&&(r.water==Gorge||r.water==scenery::Stream||r.water==Foothill||r.water==Karst||r.feature==Rocks))tags|=salvage::stony;
  if(!inland||landing)tags|=salvage::maritime;
  if(!inland&&(r.water==Headland||r.water==Island||r.water==Karst))tags|=salvage::rockyCoast;
  if(!inland&&r.water==Estuary)tags|=salvage::estuary;
  return tags;
}
inline int recoveredItem(int place,int pool,uint32_t ticket){
  const auto tags=recoveryHabitats(place,pool);
  int eligible[salvage::count],n=0;
  for(int i=0;i<salvage::count;i++)if(salvage::items[i].habitats&tags)eligible[n++]=i;
  return eligible[(ticket>>10)%n];
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
