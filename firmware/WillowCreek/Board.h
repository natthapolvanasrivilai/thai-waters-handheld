#pragma once
#include "Creek.h"
#include <Arduino_GFX_Library.h>
extern Arduino_Canvas screen;
extern bool screenOK,imuOK,powerOK,chargeLampOK;
enum class Field { Missing, Weak, Strong, NoMagnet, Good };
struct BatteryReading {
  bool valid=false, present=false, usb=false, charging=false;
  int percent=-1;
};
inline BatteryReading batteryFromStatus(uint8_t status, uint8_t state, int gauge){
  BatteryReading b;
  b.valid=true;
  b.present=(status & 0x08)!=0;
  b.usb=(status & 0x20)!=0 && (state & 0x08)==0;
  b.charging=b.present && b.usb && (state >> 5)==1;
  if(b.present && gauge>=0 && gauge<=100)b.percent=gauge;
  return b;
}
BatteryReading readBattery();
void beginBoard();
bool acceleration(creek::Vec& gravity);
Field readWheel(int& raw);
bool touchPoint(int& x,int& y);
