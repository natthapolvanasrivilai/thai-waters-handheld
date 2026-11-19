#pragma once
#include <cstdint>
namespace salvage {
enum Habitat : uint16_t {any=1,bank=2,landing=4,stony=8,flow=16,landingInland=32,still=64,maritime=128,rockyCoast=256,estuary=512};
struct Item{const char* name;const char* group;float turns;uint16_t habitats;};
constexpr Item items[]={
{"Waterlogged sandal","Litter",1.10f,bank|landing},
{"Tangled line","Lost tackle",1.00f,any},
{"Dented cup","Litter",1.30f,landing},
{"Cracked float","Lost tackle",0.95f,any},
{"Forked branch","Natural debris",1.50f,bank},
{"Line-wrapped pebble","Natural debris",1.90f,stony},
{"Split bamboo","Natural debris",1.40f,flow|landingInland},
{"Dry lotus pod","Natural debris",0.85f,still},
{"Crushed bottle","Litter",1.05f,landing},
{"Frayed mooring rope","Lost gear",1.70f,maritime},
{"Barnacled stone","Natural debris",1.95f,rockyCoast},
{"Mangrove driftwood","Natural debris",1.55f,estuary}
};
constexpr int count=sizeof(items)/sizeof(items[0]);
}
