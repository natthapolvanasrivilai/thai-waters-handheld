#pragma once
#include "Creek.h"

namespace creek {
inline const char* fightInstruction(const Game& g){
  if(g.holdingBottom())return "Holding bottom - lift or ease";
  if(g.beat()==FightBeat::Slack)return "Slack line - wind now";
  switch(g.fightStyle()){
    case FightStyle::Picker:return g.surge()?"Short tugs - ease off":"Light pull - wind gently";
    case FightStyle::Anchor:return "Weight lifting - gain line";
    case FightStyle::Sprinter:return g.surge()?"Fast run - give line":"Run slowing - gain line";
    default:return g.surge()?"Run - ease off":"Fish turning - gain line";
  }
}
}
