#include "../../firmware/WillowCreek/Landscape.h"

namespace {
uint8_t indexed[scenery::width*scenery::height];
scenery::Color palette[scenery::colorCount];
}
extern "C" {
uint8_t* paintPlace(int place,int period){
  scenery::render({indexed},palette,place,period);
  return indexed;
}
uint32_t* placePalette(){return palette;}
}
