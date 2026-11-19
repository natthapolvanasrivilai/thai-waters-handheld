#pragma once
#include <stdint.h>

namespace creek {
enum class LandingReward : uint8_t { Catch, PersonalBest, Discovery, TacklePoint };

struct LandingCue {
  uint8_t tier=255;
  LandingReward reward=LandingReward::Catch;
  bool active() const {return tier<6;}
};
}
