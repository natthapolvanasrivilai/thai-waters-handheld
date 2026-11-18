#pragma once
#include <stdint.h>
struct SoundSettings {
  uint8_t music=0; // adaptive, drift, melody, off
  uint8_t volume=2; // 0 to 3
  uint8_t cue=0; // both, visual, tone
  uint8_t cueVolume=2;
  uint8_t site=0,arrangement=0; bool reverse=false;
  bool valid() const {return music<4 && volume<4 && cue<3 && cueVolume<4;}
};
bool startSound();
void setSound(const SoundSettings& settings, bool fighting, bool bite);

