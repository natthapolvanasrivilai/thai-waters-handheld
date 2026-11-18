#include "Scene.h"
#include "Rumble.h"
#include "Connected.h"
#include <Preferences.h>
#include <esp_system.h>

using namespace creek;
namespace {
View view;
Preferences store;
Calibration setupPose{};
Gesture rod;
Wheel wheel;
Vec filtered{},lastStable{};
bool hasFilter=false,held=false;
uint32_t steadySince=0,lastTick=0,lastDraw=0,lastTouch=0,lastDown=0;
bool everDrawn=false;
Page returnTo=Page::Play;
RumblePlan haptics;
uint32_t audition=0,lastDirection=0;
bool auditioning=false, wasHapticPlay=false;
void saveBook(){view.saveFailed=store.putBytes("atlas-3",&view.game.progress,sizeof(Progress))!=sizeof(Progress);}
void togglePractice(){view.practice=!view.practice;view.game.enter(Phase::Ready);}
void setCueLevel(){view.sound.cueVolume=(view.sound.cueVolume+1)%4;store.putUChar("cuevol",view.sound.cueVolume);}


void restore(){
  store.begin("willow-v1",false);
  if(store.getBytesLength("poses")==sizeof(Calibration))store.getBytes("poses",&setupPose,sizeof(setupPose));
  view.calibrated=setupPose.valid();
  if(store.getBytesLength("atlas-3")==sizeof(Progress))store.getBytes("atlas-3",&view.game.progress,sizeof(Progress));
  else {
    struct Legacy {Entry entries[40]; uint8_t rank[3],reserved;};
    Legacy old{};
    if(store.getBytesLength("atlas-2")==sizeof(old) && store.getBytes("atlas-2",&old,sizeof(old))==sizeof(old)){
      std::copy(old.entries,old.entries+40,view.game.progress.book.entries);
      std::copy(old.rank,old.rank+3,view.game.progress.rank);saveBook();
    }
  }
  view.timeMode=store.getUChar("time-mode",4)%5;view.rodFinish=store.getUChar("finish",0)%3;
  view.game.timeSlot=view.timeMode<4?view.timeMode:0;
  view.destination=store.getUChar("spot",store.getUChar("water",0)%4)%destinationCount;view.game.site=destinations[view.destination].pool;view.sound.arrangement=view.destination;
  view.rumble=store.getUChar("rumble",0)%4;
  view.page=view.calibrated?Page::Play:Page::Rest;
  view.sound.music=store.getUChar("music",0);view.sound.volume=store.getUChar("volume",2);
  view.sound.cue=store.getUChar("cue",0);view.sound.cueVolume=store.getUChar("cuevol",2);
  view.sound.reverse=store.getBool("reverse",false);
  if(!view.sound.valid())view.sound=SoundSettings{};view.sound.site=view.game.site%4;
}
void playPage(){
  view.page=(view.practice||view.calibrated)?Page::Play:Page::Rest;
  rod=Gesture{};wheel.previous=-1;
}
void change(int x,int y,bool& practiceTap){
  if((view.page==Page::Play||view.page==Page::Rest||view.page==Page::Raise) && y<40 && x>=365){
    returnTo=view.page;view.page=Page::Hub;rod=Gesture{};stopRumble();return;
  }
  if(view.page==Page::Hub){
    if(y<40 && x>=365){view.page=returnTo;if(view.page==Page::Play)playPage();return;}
    if(y>=288){view.page=Page::Network;return;}
    if(y<42)return;
    switch((y-42)/41){
    case 0:view.pendingSite=view.destination;view.spotPage=view.destination/4;view.pendingTime=view.timeMode;view.page=Page::Waters;break;
    case 1:view.page=Page::Book;view.bookPage=view.game.site*2;break;
    case 2:view.page=Page::Journey;view.notice="First find earns 1 point, then every 3 new species.";view.refundConfirm=false;break;
    case 3:if(!view.driver)view.driver=initRumble();view.page=Page::Bench;view.casts=view.lifts=0;view.turns=0;view.direction=0;view.benchEvent="Hold in playing position";rod=Gesture{};wheel.previous=-1;break;
    case 4:view.page=Page::Options;break;
    case 5:togglePractice();playPage();break;
    }return;
  }
  if(view.page==Page::Network||view.page==Page::Bench||view.page==Page::Book||view.page==Page::Journey||view.page==Page::Waters||view.page==Page::Options){
    if(y<40 && x>=365){if(view.page==Page::Network)stopPairing();view.page=Page::Hub;auditioning=false;stopRumble();return;}
  }
  if(view.page==Page::Network){
    if(y>=157 && y<201)startPairing();
    else if(y>=202&&y<246)checkUpdate();
    else if(y>=247&&y<283)toggleRadio();
    else if(y>=283)toggleEvent();
    return;
  }
  if(view.page==Page::Waters){
    if(y>=42&&y<210)view.pendingSite=std::min(destinationCount-1,view.spotPage*4+(y-42)/42);
    else if(y>=215&&y<263)view.pendingTime=std::min(4,x/96);
    else if(y>=270){
      if(x<100||x>=380){int pages=(destinationCount+3)/4;view.spotPage=(view.spotPage+(x<100?pages-1:1))%pages;return;}
      if(view.pendingSite!=view.destination||view.pendingTime!=view.timeMode)view.game.enter(Phase::Ready);
      view.destination=view.pendingSite;view.game.site=destinations[view.destination].pool;view.sound.site=view.game.site%4;view.sound.arrangement=view.destination;view.timeMode=view.pendingTime;
      store.putUChar("spot",view.destination);store.putUChar("time-mode",view.timeMode);
      view.game.timeSlot=view.timeMode==4?pondPeriod():view.timeMode;playPage();
    }return;
  }
  if(view.page==Page::Book){
    if(y>=272){if(x<147)view.bookPage=(view.bookPage+9)%10;else if(x>=330)view.bookPage=(view.bookPage+1)%10;}return;
  }
  if(view.page==Page::Journey){
    if(y>=93&&y<237){int i=(y-93)/48;view.refundConfirm=false;
      if(view.game.progress.upgrade(i)){saveBook();view.notice="Upgrade fitted.";}
      else view.notice=view.game.progress.rank[i]>=3?"Maximum rank.":view.game.progress.rank[i]>=view.game.progress.chapter()?"Advance the story to open this rank.":"Discover more species to earn points.";
    } else if(y>=249&&y<291&&x<230){view.rodFinish=(view.rodFinish+1)%3;store.putUChar("finish",view.rodFinish);view.refundConfirm=false;}
    else if(y>=249&&y<291){if(view.refundConfirm){view.game.progress.retrain();saveBook();view.notice="Points returned. Choose a new setup.";}view.refundConfirm=!view.refundConfirm;}return;
  }
  if(view.page==Page::Bench){
    if(y>=166&&y<197){view.sound.reverse=!view.sound.reverse;store.putBool("reverse",view.sound.reverse);view.turns=0;view.direction=0;wheel.previous=-1;}
    else if(y>=197&&y<233){if(x<233)setCueLevel();else{auditioning=true;audition=millis();SoundSettings sample=view.sound;sample.cue=0;setSound(sample,false,true);}}
    else if(y>=233&&y<274){if(x<157){view.rumble=(view.rumble+1)%4;store.putUChar("rumble",view.rumble);stopRumble();}
      else {Pulse test=x<266?Pulse::Tease:x<368?Pulse::Bite:Pulse::Pull;view.driver=driveRumble(test,view.rumble,.8f);view.benchEvent=!view.driver?"Driver absent":!view.rumble?"Rumble off":test==Pulse::Tease?"Tease audition":test==Pulse::Bite?"Bite audition":"Pull audition";}}
    return;
  }
  if(view.page==Page::Options){
    if(y<42 || y>=301)return;
    bool preview=false;
    switch((y-42)/37){
    case 0:view.sound.music=(view.sound.music+1)%4;store.putUChar("music",view.sound.music);break;
    case 1:view.sound.volume=(view.sound.volume+1)%4;store.putUChar("volume",view.sound.volume);break;
    case 2:view.sound.cue=(view.sound.cue+1)%3;store.putUChar("cue",view.sound.cue);preview=true;break;
    case 3:setCueLevel();preview=true;break;
    case 4:view.sound.reverse=!view.sound.reverse;store.putBool("reverse",view.sound.reverse);wheel.previous=-1;break;
    case 5:view.practice=!view.practice;view.game.enter(Phase::Ready);playPage();return;
    case 6:view.practice=false;view.page=Page::Rest;view.badPose=false;rod=Gesture{};return;
    }
    setSound(view.sound,false,preview);return;
  }
  if(view.page==Page::Rest||view.page==Page::Raise){
    if(y<222 || y>293 || !view.stable)return;
    if(view.page==Page::Rest){lastStable=unit(filtered);view.page=Page::Raise;view.badPose=false;}
    else {
      Calibration trial{lastStable,unit(filtered)};
      if(!trial.valid()){view.badPose=true;return;}
      setupPose=trial;store.putBytes("poses",&setupPose,sizeof(setupPose));view.calibrated=true;
      view.game.enter(Phase::Ready);playPage();
    }
    return;
  }
  if(view.practice && y>=245)practiceTap=true;
}
void sampleRod(uint32_t now,uint32_t dt){
  Vec raw{};view.motion=acceleration(raw);
  if(!view.motion){hasFilter=false;view.stable=false;steadySince=now;rod=Gesture{};return;}
  float len=dot(raw,raw);view.accelG=std::sqrt(len);
  if(len<.67f || len>1.43f){
    view.stable=false;steadySince=now;rod.cast=rod.rise=false;return;
  }
  raw=unit(raw);
  if(!hasFilter){filtered=raw;steadySince=now;hasFilter=true;}
  if(dot(raw,filtered)<.9975f)steadySince=now;
  float alpha=limit(dt/(55.f+dt),0,1);
  filtered=unit({filtered.x+alpha*(raw.x-filtered.x),filtered.y+alpha*(raw.y-filtered.y),filtered.z+alpha*(raw.z-filtered.z)});
  view.stable=now-steadySince>=420;
  if(((view.page==Page::Play && !view.practice)||view.page==Page::Bench) && view.calibrated){
    view.degrees=setupPose.tilt(filtered);view.span=setupPose.span();
    rod.sample(view.degrees,view.span,now);view.raised=rod.high;
  } else {rod=Gesture{};view.raised=false;}
}
}
void setup(){
  Serial.begin(115200);restore();view.game.seed=esp_random();beginBoard();beginConnected();view.driver=initRumble();beginScene();
  view.audio=startSound();setSound(view.sound,false,false);
  Serial.printf("Thai Waters 0.3 | LCD %d IMU %d audio %d charge config 4.20V/300mA readback %d\n",screenOK,imuOK,view.audio,powerOK);
  lastTick=millis();paint(view);confirmUpdateHealth(screenOK && imuOK && powerOK && view.audio);
}
void loop(){
  uint32_t now=millis(),dt=now-lastTick;
  if(dt<12){delay(1);return;}
  lastTick=now;dt=std::min<uint32_t>(dt,100);view.time=now;
  tickConnected();eventTick(view.destination);
  if(view.timeMode==4 && !view.game.running())view.game.timeSlot=pondPeriod();
  sampleRod(now,dt);
  int angle=0;view.field=readWheel(angle);
  float turns=wheel.read(angle,view.field==Field::Good,now,view.sound.reverse);
  if(view.page==Page::Bench){
    view.raw=view.field==Field::Good?angle:-1;view.turns+=turns;
    if(std::abs(turns)>.0009f){view.direction=turns>0?1:-1;lastDirection=now;}
    else if(now-lastDirection>350)view.direction=0;
    if(rod.rise){++view.lifts;view.benchEvent="LIFT detected";}
    if(rod.cast){++view.casts;view.benchEvent="CAST detected";}
  }
  bool tap=false;
  if(now-lastTouch>=24){
    lastTouch=now;int x,y;bool down=touchPoint(x,y);
    if(down){lastDown=now;if(!held)change(x,y,tap);held=true;}
    else if(now-lastDown>=45)held=false;
  }
  Phase before=view.game.phase;
  if(view.page==Page::Play && (view.practice||(view.motion&&view.field==Field::Good))){
    view.game.tick(dt,view.practice?tap:rod.cast,view.practice?tap:rod.rise,view.practice?(tap?.25f:0):turns);
  } else if(view.page==Page::Play)rod=Gesture{};
  if(view.game.phase!=before){
    Serial.printf("phase=%u catch=%d line=%.2f\n",unsigned(view.game.phase),view.game.catches,view.game.line);
  }
  if(before!=view.game.phase && view.game.phase==Phase::Landed){saveBook();eventCatch();}
  bool active=view.page==Page::Play && (view.practice||(view.motion&&view.field==Field::Good));
  if(wasHapticPlay&&!active)stopRumble();
  wasHapticPlay=active;
  Pulse pulse=haptics.tick(view.game,now,active);
  if(pulse!=Pulse::None)view.driver=driveRumble(pulse,view.rumble,view.game.heat);
  if(auditioning && now-audition>=420)auditioning=false;
  SoundSettings mix=view.sound;if(auditioning)mix.cue=0;
  setSound(mix,active && view.game.phase==Phase::Fight,view.game.phase!=before&&view.game.phase==Phase::Bite);
  if(!everDrawn||now-lastDraw>=55){lastDraw=now;everDrawn=true;paint(view);}
}


