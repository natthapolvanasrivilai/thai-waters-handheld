#include "../WillowCreek/WillowCreek.ino"
#include <cassert>
#include <cstdio>
uint32_t testClock=0;Arduino_Canvas screen;bool screenOK=true,imuOK=true,powerOK=true;
creek::Vec inputG{0,0,1};int encoder=4070,px=0,py=0,cuePulses=0,motorPulses=0;
bool touched=false;Field magnet=Field::Good;SoundSettings lastMix;
BatteryReading readBattery(){return batteryFromStatus(0x28,0x20,57);}
void beginBoard(){} bool acceleration(creek::Vec& v){v=inputG;return true;}
Field readWheel(int& a){a=encoder;return magnet;}
bool touchPoint(int& x,int& y){x=px;y=py;return touched;}
void beginScene(){}void paint(const View&){}
bool startSound(){return true;}void setSound(const SoundSettings& s,bool,bool cue,int){lastMix=s;if(cue)++cuePulses;}
bool initRumble(){return true;}bool driveRumble(Pulse p,uint8_t level,float){if(p!=Pulse::None && level)++motorPulses;return true;}void stopRumble(){}
void beginConnected(){}void tickConnected(){}void startPairing(){}void stopPairing(){}void toggleRadio(){}void checkUpdate(){}int pondPeriod(){return 1;}
void confirmUpdateHealth(bool){}void eventTick(int){}void eventCatch(){}void toggleEvent(){}
void step(int count){while(count--){testClock+=16;loop();}}
void tap(int x,int y){px=x;py=y;touched=true;step(3);touched=false;step(4);}
int main(){
 assert(readBattery().present && readBattery().charging && readBattery().percent==57);
 auto usb=batteryFromStatus(0x20,0,39);assert(usb.usb&&!usb.present&&!usb.charging&&usb.percent<0);
 auto bad=batteryFromStatus(8,0,127);assert(bad.present&&!bad.usb&&bad.percent<0);
 auto low=batteryFromStatus(8,0,0);assert(low.percent==0&&!low.charging);
 struct Legacy{Entry entries[40];uint8_t rank[3],pad;};Legacy old{};old.entries[4].count=2;old.entries[4].best=20;store.putBytes("atlas-2",&old,sizeof(old));setup();assert(view.game.progress.book.entries[4].count==2);step(42);assert(view.page==Page::Rest&&view.stable);
 tap(120,250);inputG={0,.64f,.7684f};step(55);tap(125,250);assert(view.calibrated&&view.page==Page::Play);
 inputG={0,0,1};step(30);tap(420,16);tap(2,20);assert(view.page==Page::Play);tap(420,16);tap(67,174);assert(view.page==Page::Bench);
 tap(360,307);assert(view.page==Page::TouchCheck);
 tap(463,303);assert(view.touchStep==0);
 for(int i=0;i<9;i++){tap(touchColumn[i%3],touchRow[i/3]);assert(view.touchStep==i+1);}
 tap(90,302);assert(view.page==Page::Bench);
 step(25);inputG={0,.64f,.7684f};step(20);inputG={0,0,1};step(24);
 assert(view.casts==1&&view.lifts==1&&view.degrees<2 && view.game.phase==Phase::Ready);
 encoder=35;step(1);assert(view.raw==35 && view.direction==1 && view.turns>0);
 tap(32,181);assert(view.sound.reverse);encoder=125;step(1);assert(view.direction==-1&&view.turns<0);
 magnet=Field::Weak;step(1);assert(view.raw==-1);magnet=Field::Good;encoder=4000;step(1);assert(view.turns>-.1);
 view.sound.cue=1;tap(26,211);int level=view.sound.cueVolume;tap(342,211);assert(cuePulses==1&&lastMix.cue==0&&lastMix.cueVolume==level);
 step(35);assert(lastMix.cue==1);tap(53,251);tap(345,250);assert(motorPulses==1);
 tap(427,17);tap(63,70);tap(64,143);tap(244,225);tap(240,270);assert(view.page==Page::Play && view.game.site==2 && view.sound.site==2);
 view.game.phase=Phase::Fight;view.game.fish=20;view.game.line=.01f;view.game.target=6;view.game.length=35;view.practice=true;
 tap(23,287);assert(view.game.phase==Phase::Landed && store.getBytesLength("atlas-3")==sizeof(Progress));
 tap(425,17);tap(88,145);assert(view.page==Page::Journey);tap(60,162);assert(view.game.progress.rank[1]==1);
 view.game.progress=Progress{};restore();assert(view.timeMode==2&&view.game.progress.rank[1]==1&&view.game.progress.book.entries[20].count==1&&view.calibrated);
 // Navigate every scene-backed sheet at its physical LCD coordinates.
 view.page=Page::Play;view.practice=true;view.game.phase=Phase::Fight;
 tap(420,16);assert(view.page==Page::Hub);
 uint32_t pausedAge=view.game.age;step(20);assert(view.game.age==pausedAge);
 tap(78,104);assert(view.page==Page::Book);
 int oldPage=view.bookPage;tap(405,267);assert(view.bookPage==(oldPage+1)%10);
 tap(406,43);assert(view.page==Page::Hub);
 tap(78,202);assert(view.page==Page::Options);int volume=view.sound.volume;
 tap(89,100);assert(view.sound.volume==(volume+1)%4);
 tap(406,43);tap(78,271);assert(view.page==Page::Network);
 tap(406,43);assert(view.page==Page::Hub);tap(406,43);assert(view.page==Page::Play);
 puts("PASS compact overlay touch mapping, fishing-state pause, edge dismissal and resume.");
 puts("PASS sketch-loop bench calibration, live cast/lift counts, signed wrapped encoder and reversal, magnet recovery, independent cue audition, rumble audition, travel, upgrade and saved-state restore including v0.2 journal migration and time selection.");
}
