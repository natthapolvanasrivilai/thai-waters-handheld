#pragma once
#include <cstdint>
bool beginRodController(int batteryPercent);
void endRodController();
bool rodControllerStreaming();
bool rodControllerReady();
void armRodController();
const char* rodControllerStatus();
unsigned rodPairCode();
void tickRodController(uint32_t now,bool cast,bool lift,float turns,float pitch,int batteryPercent);
