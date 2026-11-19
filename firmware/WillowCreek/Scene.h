#pragma once
#include "Board.h"
#include "Destinations.h"
#include "Sound.h"
#include "CatchLog.h"
enum class Page { Bait, Play, Arrival, Options, Rest, Raise, Hub, Waters, Book, Journey, Bench, Network, Controller, TouchCheck, BookDetail, CatchHistory };
// Player sheets share this 392 x 272 rectangle on the native landscape LCD.
namespace menuui {
constexpr int x=44,y=24,w=392,h=272,header=48;
constexpr int waterRow=49,periodY=171,travelY=221,bookNav=221,bookRows=4;
constexpr int workshopTop=82,workshopRow=53,baitRow=51,depthY=219;
constexpr int gridTop=48,gridRow=54,networkTop=109,networkRow=50,controllerTop=192,controllerRow=64;
constexpr int benchTop=164,benchRow=52;
inline int benchAction(int x,int y){
  return x>=0 && x<480 && y>=benchTop && y<320?4*((y-benchTop)/benchRow)+x/120:-1;
}
inline int gridIndex(int x,int y,int top,int height,int count){
  if(x<0 || x>=w || y<top || y>=h)return -1;
  const int cell=((y-top)/height)*2+(x>=w/2);
  return cell<count && y<top+((count+1)/2)*height?cell:-1;
}
inline bool overlay(Page p){
 return p==Page::Bait || p==Page::Hub || p==Page::Waters || p==Page::Book || p==Page::BookDetail || p==Page::CatchHistory || p==Page::Journey || p==Page::Options || p==Page::Network || p==Page::Controller;
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
  uint32_t arrivalStart=0;
  uint32_t time=0, casts=0, lifts=0;
  float accelG=0, degrees=0, span=0, turns=0; int destination=0,spotPage=0,pendingSite=0,pendingTime=4,pendingWeather=0,timeMode=4,rodFinish=0; int raw=-1, direction=0, bookPage=0, bookWater=0;
  creek::BookFilter bookFilter=creek::BookFilter::Nearby;
  int bookSpecies=-1;
  uint32_t historyCount=0;
  creek::CatchRecord history{};
  bool historyError=false;
  bool driver=false,saveFailed=false, refundConfirm=false; uint8_t rumble=0;
  const char* benchEvent="Hold in playing position";const char* notice="";

};
inline int bookTile(const View& v,int tile){
  const auto& book=v.game.progress.book;int wanted=v.bookPage*menuui::bookRows+tile;
  for(int i=0;i<creek::stockSize(v.bookWater);i++){
    int id=creek::stockId(v.bookWater,i);
    if(book.visible(id,v.destination,v.bookFilter) && wanted--==0)return id;
  }
  return -1;
}
void beginScene();
void paint(const View& v);
