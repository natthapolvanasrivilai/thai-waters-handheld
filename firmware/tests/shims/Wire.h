#pragma once
#include "Arduino_GFX_Library.h"
#include <vector>
#include <utility>
struct WireMock {
 int id=0xe0;bool nack=false;uint8_t address=0;
 std::vector<uint8_t> frame;std::vector<std::pair<int,int>> log;
 void beginTransmission(uint8_t a){address=a;frame.clear();}
 void write(uint8_t v){frame.push_back(v);}
 int endTransmission(bool stop=true){if(nack||address!=0x5a)return 2;if(frame.size()==2)log.emplace_back(frame[0],frame[1]);return 0;}
 size_t requestFrom(uint8_t a,size_t n){return a==0x5a?n:0;}
 int read(){return id;}
};
inline WireMock Wire;
