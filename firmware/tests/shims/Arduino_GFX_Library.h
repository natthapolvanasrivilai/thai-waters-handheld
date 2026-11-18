#pragma once
#include <cstdint>
#include <cstddef>
class Arduino_Canvas {};
extern uint32_t testClock;
inline uint32_t millis(){return testClock;}
inline void delay(int n){testClock+=n;}
struct Console {void begin(int){} template<class... Args> void printf(const char*,Args...){}};
inline Console Serial;
