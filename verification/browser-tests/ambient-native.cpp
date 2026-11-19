#include "../../firmware/WillowCreek/AmbientLcd.h"
#include <cstdio>
#include <cstring>
// Host-only LCD capture. Panels and reverse lookup below live exclusively in
// this verification executable. The production renderer writes to screen RAM.
static uint16_t lcd[64],clean[480*320],frame[480*320];
static uint8_t indexed[240*160],reverseLcd[65536];
int main(){
  scenery::Layout layout{};
  scenery::Color colors[64]{};
  constexpr uint32_t times[]={11000u,0xfffffe00u};
  for(int id=0;id<int(sizeof(scenery::recipes)/sizeof(scenery::Recipe));++id)for(int period=0;period<4;period++){
    scenery::render({indexed},colors,id,period,&layout);
    scenery::lcdPalette(colors,lcd);
    for(int i=0;i<57;i++)reverseLcd[lcd[i]]=uint8_t(i);
    for(int x=0;x<240;x++)for(int y=0;y<160;y++){
      int pos=scenery::LcdSpans::offset(x,y);
      uint16_t c=lcd[indexed[x*160+159-y]];
      clean[pos]=clean[pos+1]=clean[pos+320]=clean[pos+321]=c;
    }
    for(auto t:times){
      std::memcpy(frame,clean,sizeof(frame));
      scenery::LcdSpans sink{frame,clean,lcd};
      scenery::paintAmbient(sink,layout,t);
      uint32_t digest=2166136261u;
      for(int x=0;x<240;x++)for(int y=159;y>=0;y--){
        int pos=scenery::LcdSpans::offset(x,y);
        uint16_t c=frame[pos];
        if(frame[pos+1]!=c||frame[pos+320]!=c||frame[pos+321]!=c)return 1;
        digest=(digest^reverseLcd[c])*16777619u;
      }
      std::printf("%08x\n",unsigned(digest));
    }
  }
}
