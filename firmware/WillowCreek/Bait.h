#pragma once
#include "Waters.h"
#include "FishProfiles.h"
namespace creek {
static_assert(sizeof(dietForSpecies)==fishCount,"Regenerate the species profiles with the encounter table");
constexpr int baitCount=18;
constexpr const char* baitNames[]={"River worm","Raw shrimp","Fermented rice / rum bran","Surface insect","Live baitfish","Squid strip"};
constexpr const char* depthNames[]={"Surface","Midwater","Bottom"};
struct Diet {uint8_t foods,depths,preferred;};
// Bit masks restrict food and depth independently. The preferred rig earns four tickets.
constexpr Diet diets[]={
 {15,7,6},   // Bank omnivores: worm, shrimp, bran or insects
 {5,6,8},    // Grazing carp: midwater bran
 {9,1,3},    // Insect feeders: surface insects or worm
 {3,4,13},   // Prawn and invertivores: bottom shrimp or worm
 {18,6,10},  // Ambush predators: live fish or shrimp
 {50,4,17},  // Benthic sea predators: squid, shrimp or fish on bottom
 {20,3,2},   // Schooling fish: suspended feed or baitfish
 {3,6,7},    // Small crustacean feeders
 {48,3,10},  // Fast marine predators: baitfish or squid
 {7,4,12}    // Mud and gravel foragers
};
inline int preferredChoice(int id){return id>=0&&id<fishCount?diets[dietForSpecies[id]].preferred:0;}
inline int baitWeightFor(int id,int choice,int /*rig*/){
 if(id<0||id>=fishCount||choice<0||choice>=baitCount)return 0;
 const auto d=diets[dietForSpecies[id]];
 if(!(d.foods&(1u<<(choice%6))) || !(d.depths&(1u<<(choice/6))))return 0;
 return choice==d.preferred?4:1;
}
}
