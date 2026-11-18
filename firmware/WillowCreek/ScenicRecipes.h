#pragma once
#include <stdint.h>
namespace scenery {
enum Water : uint8_t { Lake, Bend, Karst, Wide, Gorge, Stream, Marsh, Foothill, Estuary, Gulf, Island, Headland };
enum Feature : uint8_t { Raft, Ferry, Paper, Bridge, Marker, Boat, Basket, Rocks, Roots, Ford, Pier, Reeds, Kitchen, Lantern, Market, Heron, Lotus, Snag, Boathouse, Rail, Nets, Lamps, Buoy, Sail };
struct Recipe { Water water; Feature feature; };
// Stable destination order matches game/locations.json. Each pair directs the
// composition; the stable place ID selects its shore geometry and viewing angle.
constexpr Recipe recipes[] = {
  {Lake,Raft}, {Wide,Ferry}, {Karst,Paper}, {Wide,Bridge}, {Gorge,Marker},
  {Bend,Ferry}, {Foothill,Basket}, {Gorge,Rocks}, {Stream,Roots}, {Bend,Ford},
  {Foothill,Ford}, {Bend,Boat}, {Bend,Reeds}, {Marsh,Kitchen}, {Bend,Basket}, {Bend,Lantern},
  {Lake,Market}, {Marsh,Boat}, {Lake,Pier}, {Lake,Raft}, {Foothill,Lantern},
  {Foothill,Ferry}, {Bend,Basket}, {Marsh,Heron}, {Wide,Paper}, {Foothill,Bridge},
  {Bend,Pier}, {Wide,Reeds}, {Bend,Market}, {Bend,Snag}, {Gorge,Boat},
  {Lake,Kitchen}, {Lake,Boat}, {Lake,Marker}, {Marsh,Lotus}, {Marsh,Reeds}, {Marsh,Heron},
  {Wide,Ferry}, {Foothill,Bridge}, {Foothill,Lantern}, {Bend,Basket}, {Bend,Marker},
  {Bend,Ferry}, {Wide,Market}, {Marsh,Reeds}, {Gorge,Snag}, {Lake,Raft},
  {Lake,Pier}, {Lake,Boat}, {Lake,Heron}, {Lake,Boathouse}, {Lake,Buoy},
  {Wide,Market}, {Stream,Marker}, {Foothill,Basket}, {Gorge,Rocks}, {Gorge,Raft},
  {Lake,Boathouse}, {Foothill,Pier}, {Bend,Paper}, {Gorge,Raft}, {Foothill,Boathouse},
  {Lake,Boat}, {Wide,Market}, {Foothill,Rocks}, {Bend,Marker}, {Marsh,Reeds},
  {Bend,Market}, {Wide,Boat}, {Stream,Snag}, {Gorge,Lantern}, {Lake,Marker},
  {Marsh,Lotus}, {Wide,Pier}, {Wide,Ferry}, {Marsh,Reeds}, {Wide,Kitchen},
  {Foothill,Paper}, {Bend,Ferry}, {Foothill,Reeds}, {Stream,Lotus}, {Lake,Rail},
  {Wide,Market}, {Lake,Ferry}, {Wide,Lamps}, {Gorge,Pier}, {Gorge,Raft},
  {Karst,Boat}, {Foothill,Paper}, {Gorge,Rocks}, {Lake,Rocks}, {Lake,Boathouse},
  {Lake,Marker}, {Island,Raft}, {Foothill,Pier}, {Gorge,Kitchen},
  {Island,Lamps}, {Estuary,Raft}, {Gulf,Lamps}, {Headland,Pier}, {Estuary,Buoy},
  {Estuary,Boat}, {Estuary,Nets}, {Gulf,Marker}, {Headland,Lamps}, {Island,Boat},
  {Gulf,Boat}, {Headland,Buoy}, {Gulf,Ferry}, {Gulf,Sail}, {Gulf,Lantern},
  {Island,Pier}, {Karst,Boat}, {Headland,Nets}, {Karst,Sail}, {Island,Sail}, {Island,Marker}
};
}
