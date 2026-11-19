#pragma once
#include "SpecimenIndex.h"

namespace specimen {
#ifdef ARDUINO
inline const uint8_t* cardPixels=nullptr;
void loadCardArt();
#else
// The standalone browser copies its embedded bank into WASM memory before gameplay.
inline uint8_t browserPixels[cardBytes?cardBytes:1];
inline const uint8_t* cardPixels=browserPixels;
inline void loadCardArt(){}
#endif
inline bool has(int id){
 if(id<0||id>=int(sizeof(index)/sizeof(index[0])))return false;
 return id<60||(index[id]>=0&&(index[id]<residentFrames||cardPixels));
}
}
