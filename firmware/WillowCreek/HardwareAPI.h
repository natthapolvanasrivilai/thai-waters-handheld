#pragma once
#include "Board.h"
#include <SensorQMI8658.hpp>
#define XPOWERS_CHIP_AXP2101
#include <XPowersLib.h>
#include <Wire.h>
namespace hardware {
constexpr unsigned apiMajor=1, apiMinor=0;
SensorQMI8658& motion();
XPowersPMU& power();
TwoWire& bus();
bool gyroPower(bool enabled);
struct Sample{
  uint32_t uptimeMs;creek::Vec accelG,gyroDps;int16_t accelRaw[3],gyroRaw[3];
  bool accelOK,gyroOK,accelRawOK,gyroRawOK;Field field;int reel;
};
Sample sample();
}

