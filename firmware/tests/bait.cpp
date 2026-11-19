#include "../WillowCreek/Creek.h"
#include "../WillowCreek/Rumble.h"
#include <cassert>
#include <cstdio>
using namespace creek;

static Game start(unsigned seed,int place,int time,int bait){
    Game g;
    g.beginSession(seed);
    g.destination=place;
    g.site=destinations[place].pool;
    g.timeSlot=time;
    g.arriveAt(place);
    assert(g.setBait(bait));
    for(int x=10;x<=90;x+=5){
        g.setAim(x*.01f,.65f);
        if(g.featureAt(g.aimX,g.aimY)==ClearWater)break;
    }
    assert(g.featureAt(g.aimX,g.aimY)==ClearWater);
    return g;
}

int main(){
    assert(preferredChoice(prawn)==13);
    unsigned prawnSeed=0;
    for(unsigned seed=1;seed<=2048;seed++){
        Game surface=start(seed,1,2,1);
        surface.tick(16,true,false,0);
        assert(surface.emptyCast || surface.fish!=prawn);
        Game bottom=start(seed,1,2,13);
        bottom.tick(16,true,false,0);
        if(!bottom.emptyCast && bottom.fish==prawn && !prawnSeed)prawnSeed=seed;
    }
    assert(prawnSeed);
    Game hooked=start(prawnSeed,1,2,13);
    hooked.tick(16,true,false,0);hooked.tick(650,false,false,0);
    assert(hooked.phase==Phase::Waiting && !hooked.setBait(1));
    hooked.tick(hooked.waitMs,false,false,0);assert(hooked.phase==Phase::Bite);
    hooked.tick(16,false,true,0);assert(hooked.phase==Phase::Fight);
    // Local diet and time windows may allow another fish even if the target
    // rejects the bait. Find a genuinely empty combination for the cue test.
    for(int place=0;place<destinationCount;place++)for(int time=0;time<4;time++)for(int bait=0;bait<baitCount;bait++){
        Game dry=start(19,place,time,bait);
        dry.tick(16,true,false,0);
        if(!dry.emptyCast)continue;
        RumblePlan haptics;
        assert(dry.length==0 && !dry.fileCatch());
        dry.tick(650,false,false,0);
        for(unsigned t=0;t<8000 && dry.phase==Phase::Waiting;t+=50){
            assert(!dry.teasing() && haptics.tick(dry,t,true)==Pulse::None);
            dry.tick(50,false,false,0);
        }
        assert(dry.phase==Phase::Lost && dry.reason==Reason::NoBite);
        assert(!dry.fileCatch() && dry.catches==0 && dry.progress.book.discovered()==0 && dry.progress.points()==0);
        printf("PASS surface shrimp excludes prawn in 2048 normal casts; bottom prawn seed %u. Empty cast at place %d time %d bait %d has no bite, cue, catch or points.\n",prawnSeed,place,time,bait);
        return 0;
    }
    assert(false && "Expected an incompatible local bait/depth combination");
}
