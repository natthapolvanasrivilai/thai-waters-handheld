#pragma once
#include "Board.h"
#include "Destinations.h"
#include "Sound.h"
enum class Page { Play, Options, Rest, Raise, Hub, Waters, Book, Journey, Bench, Network, TouchCheck };
// Player sheets share this 392 x 272 rectangle on the native landscape LCD.
namespace menuui {
constexpr int x=44,y=24,w=392,h=272,header=32,hubRow=33,optionRow=28;
constexpr int waterRow=37,periodY=190,travelY=230,bookNav=230;
constexpr int rigY=54,upgradeY=92,upgradeRow=36,finishY=205;
inline bool overlay(Page p){
 return p==Page::Hub || p==Page::Waters || p==Page::Book || p==Page::Journey || p==Page::Options || p==Page::Network;
}
inline bool inside(int px,int py){return px>=x && px<x+w && py>=y && py<y+h;}
}
constexpr int touchColumn[]={16,240,463}, touchRow[]={16,160,303};
struct View {
  creek::Game game;
  SoundSettings sound;
  BatteryReading battery;
  Page page=Page::Rest;
  uint8_t touchStep=0;
  int lastTouchX=-1,lastTouchY=-1;
  Field field=Field::Missing;
  bool practice=false, audio=false, motion=false, stable=false, badPose=false, raised=false, calibrated=false;
  uint32_t time=0, casts=0, lifts=0;
  float accelG=0, degrees=0, span=0, turns=0; int destination=0,spotPage=0,pendingSite=0,pendingTime=4,timeMode=4,rodFinish=0; int raw=-1, direction=0, bookPage=0;
  bool driver=false,saveFailed=false, refundConfirm=false; uint8_t rumble=0;
  const char* benchEvent="Hold in playing position";const char* notice="";

};
void beginScene();
void paint(const View& v);
