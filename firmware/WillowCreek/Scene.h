#pragma once
#include "Board.h"
#include "Destinations.h"
#include "Sound.h"
enum class Page { Play, Options, Rest, Raise, Hub, Waters, Book, Journey, Bench, Network };
struct View {
  creek::Game game;
  SoundSettings sound;
  Page page=Page::Rest;
  Field field=Field::Missing;
  bool practice=false, audio=false, motion=false, stable=false, badPose=false, raised=false, calibrated=false;
  uint32_t time=0, casts=0, lifts=0;
  float accelG=0, degrees=0, span=0, turns=0; int destination=0,spotPage=0,pendingSite=0,pendingTime=4,timeMode=4,rodFinish=0; int raw=-1, direction=0, bookPage=0;
  bool driver=false,saveFailed=false, refundConfirm=false; uint8_t rumble=0;
  const char* benchEvent="Hold in playing position";const char* notice="";

};
void beginScene();
void paint(const View& v);
