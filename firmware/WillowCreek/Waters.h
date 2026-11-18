#pragma once
#include <cstdint>
namespace creek {
constexpr int siteCount=5, fishCount=52, perSite=10;
struct Site {const char *name,*track,*water;};
constexpr Site sites[]={
{"Mae Ngat Reservoir","Lotus at Dawn","Pond"},
{"Chao Phraya","Ferry Lanterns","River"},
{"Cheow Lan Lake","Karst Echo","Lake"},
{"Nong Khai Mekong","Mekong Afterglow","River"},
{"Coastal waters","Saltwind","Sea"},
};
constexpr const char* ranks[]={"Common","Uncommon","Rare","Epic","Legendary"};
constexpr const char* times[]={"Dawn","Day","Dusk","Night"};
constexpr const char* finishes[]={"River reed","Copper","Kingfisher"};
struct Species {const char* name; uint8_t low,high,tier,weight,form,factor;const char* lore;};
constexpr Species catalog[]={
{"Climbing perch",9,23,0,16,0,14,"Hatched in the lotus roots beside the potter's steps."},
{"Three-spot gourami",8,16,0,16,0,15,"Raised in the reed beds behind the blue pavilion."},
{"Silver barb",15,35,0,16,0,16,"Followed the first monsoon into the orchard pond."},
{"Walking catfish",19,41,1,7,2,13,"Slipped in through a flooded rice-field gate."},
{"Snakeskin gourami",13,25,1,7,0,14,"Grew up beneath the lotus seller's floating basket."},
{"Nile tilapia",18,43,1,7,0,15,"Came from the little pond behind the clay kiln."},
{"Striped snakehead",25,66,2,3,1,10,"Kept watch in the water lilies of the north inlet."},
{"Broadhead catfish",20,38,2,3,2,13,"Hid among the roots of the old tamarind tree."},
{"Marbled goby",21,50,3,2,1,8,"Born in the gravel shallows below the millstone."},
{"Giant gourami",37,68,4,1,0,15,"Once sheltered in the shade of a floating shrine."},
{"Redtail botia",12,24,0,16,0,16,"Grew up under a ferry landing's worn timber steps."},
{"Tinfoil barb",14,34,0,16,0,17,"Ran silver with a shoal from the lantern quay."},
{"Banded mystus",9,22,0,16,2,10,"Born where a rope ferry used to cross the current."},
{"Siamese mud carp",18,47,1,7,0,15,"Grazed the silt beside the old brickworks."},
{"Red-tailed tinfoil barb",18,33,1,7,0,16,"Followed the rice barges around the temple bend."},
{"Asian redtail catfish",28,84,1,7,2,13,"Kept to the deep pilings of the copper-roofed wharf."},
{"Soldier river barb",24,62,2,3,0,14,"Came downriver through the boatbuilders' reach."},
{"Bronze featherback",22,53,2,3,1,9,"Grew up in the backwater behind a ferry island."},
{"Clown featherback",39,91,3,2,1,10,"Made its home in the shadow of a sunken skiff."},
{"Giant barb",65,165,4,1,0,17,"Returned each flood to the bell tower's reflection."},
{"Hampala barb",18,63,0,16,0,14,"Hatched in a stream that falls between two cliffs."},
{"Striped barb",7,16,0,16,0,15,"Grew up in the reed pools near a floating school."},
{"Forest snakehead",17,36,0,16,1,10,"Came from a forest creek beneath the limestone arch."},
{"Bonylip barb",14,35,1,7,0,17,"Grazed the green stones at the lake's hidden spring."},
{"Spotted barb",9,19,1,7,0,14,"Sheltered among the moorings of an empty raft house."},
{"Red-tailed rasbora",8,17,1,7,1,9,"Left the fern-lined inlet with the first warm rain."},
{"Great snakehead",39,88,2,3,1,10,"Hunted in a flooded grove below the white cliff."},
{"Blue mahseer",26,72,2,3,0,17,"Rose from a cold spring beneath the karst towers."},
{"Giant snakehead",40,105,3,2,1,8,"Grew up in the shadow of a drowned fig tree."},
{"Thai mahseer",42,95,4,1,0,15,"Followed a ribbon of clear water out of the hills."},
{"Siamese glassfish",5,11,0,16,0,16,"Grew up in the shallows beside the silk dyers' bank."},
{"Asian bumblebee catfish",7,15,0,16,2,13,"Hid beneath a turned-over ferry basket."},
{"Yellow mystus",10,24,0,16,2,10,"Came from the ochre pools behind the night market."},
{"Black sharkminnow",21,73,1,7,0,15,"Patrolled a stony channel under the eastern span."},
{"Smallscale mud carp",15,34,1,7,0,16,"Followed the silt past a row of floating gardens."},
{"Siamese algae eater",8,16,1,7,1,11,"Grazed the smooth posts at the old boat crossing."},
{"Striped river catfish",36,95,2,3,2,10,"Rode the floodwater past the lantern boats."},
{"Wallago catfish",57,145,2,3,2,11,"Kept to a deep bend below the moonlit bridge."},
{"Jullien mud carp",45,110,3,2,0,16,"Came down from a gravel bar called the Silver Step."},
{"Mekong giant catfish",90,225,4,1,2,13,"Born in a deep pool the boatmen call the Blue Well."},
{"Giant river prawn",12,32,2,3,3,6,"Sheltered under the ferry piles until its claws turned blue."},
{"Giant freshwater stingray",65,240,4,1,4,8,"Left a round print on the Moonbank's silver sand."},
{"Indian mackerel",14,31,0,16,1,10,"Followed the floating ice down from a blue fishing boat."},
{"Yellowstripe scad",12,22,0,16,1,12,"Learned to turn with the school alongside a line of buoys."},
{"Indian anchovy",6,15,0,16,1,8,"Grew up where the green lamp meets the edge of the dark."},
{"Goldlined seabream",16,42,1,7,1,18,"Once sheltered beneath a buoy daubed with yellow paint."},
{"Bigeye scad",17,36,1,7,1,14,"Fed after dark near a boat the crew calls Little Moon."},
{"Talang queenfish",32,99,1,7,1,9,"Ran beside a skiff for the length of a morning song."},
{"Cobia",44,155,2,3,1,9,"Travelled in the long shade of a lost marker float."},
{"Great barracuda",46,158,2,3,1,6,"Watched the anchovy shoals from the edge of blue water."},
{"Giant trevally",55,148,3,2,1,17,"Turned the water white beside a half-submerged anchor."},
{"Indo-Pacific sailfish",110,245,4,1,1,6,"Rose like a torn blue sail beyond the last fishing light."},
};
constexpr int prawn=40, ray=41;
inline int waterOf(int id){return id>=42?4:id==prawn?1:id==ray?3:id/10;}
inline int stockSize(int water){return water==1||water==3?11:10;}
inline int stockId(int water,int slot){return water==4?42+slot:slot<10?water*10+slot:water==1?prawn:ray;}
inline int encounterWeight(int id,int time){
 if(id==prawn){constexpr int w[]={0,0,8,3};return w[time];}
 if(id==ray){constexpr int w[]={1,0,0,3};return w[time];}
 return catalog[id].weight*(id%4==time?3:2);
}
inline int weightGrams(int id,int cm){return (cm*cm*cm*catalog[id].factor+500)/1000;}
struct Entry {uint32_t count=0; uint16_t best=0; uint16_t reserved=0;};
struct Journal {
 Entry entries[fishCount]{};
 int discovered(int start=0,int end=fishCount) const {int n=0;for(int i=start;i<end;i++)n+=entries[i].count>0;return n;}
 void record(int id,int cm){auto& e=entries[id];if(e.count!=UINT32_MAX)++e.count;if(cm>e.best)e.best=cm;}
};

constexpr const char* paths[]={"Hook timing","Reel gearing","Line control"};
constexpr const char* chapters[]={"First light","First entry","Reading water","Across the map","Master angler","Atlas complete"};
constexpr const char* story[]={"Land your first fish.","Find five species.","Visit two waters and log twelve species.","Log fish in all four waters and find 26 species.","Complete the 52-species field book.","Your atlas is complete. Chase personal bests."};
constexpr const char* letters[]={"At the lotus pond, a boatkeeper gives you an empty atlas.","Your first sketch earns a place in the ferry log.","The ferryman asks for a page from a second water.","Carry the lake sketches north to the Mekong landing.","Four landings have signed your book. Fill the missing pages.","The boatkeeper binds your atlas for the next traveller."};
struct Progress {
 Journal book;
 uint8_t rank[3]{}, reserved=0;
 int waters() const {unsigned mask=0;for(int i=0;i<fishCount;i++)if(book.entries[i].count)mask|=1u<<waterOf(i);return __builtin_popcount(mask);}
 int chapter() const {
   int n=book.discovered();if(n==fishCount)return 5;if(n>=26 && waters()>=4)return 4;
   if(n>=12 && waters()>=2)return 3;if(n>=5)return 2;return n?1:0;
 }
 int points() const {
   int n=book.discovered(),p=n?1+(n-1)/3:0;
   for(int v:rank)p-=v*(v+1)/2;return p;
 }
 bool upgrade(int i){
   if(i<0||i>2||rank[i]>=3||rank[i]>=chapter()||points()<rank[i]+1)return false;
   ++rank[i];return true;
 }
 void retrain(){for(auto& v:rank)v=0;}
};
}

