#include "Scene.h"
#include "Arrival.h"
#include "JournalDisk.h"
#include "Rumble.h"
#include "ReelDetents.h"
#include "Connected.h"
#include <Preferences.h>
#include <esp_system.h>
#include <ctime>

using namespace creek;
namespace {
View view;
Preferences store;
Calibration setupPose{};
Gesture rod;
Wheel wheel;
Vec filtered{},lastStable{};
bool hasFilter=false,held=false;
uint32_t steadySince=0,lastTick=0,lastDraw=0,lastTouch=0,lastDown=0,lastBattery=0;
bool everDrawn=false;unsigned landedDay=0;
// A unit without a synced RTC keeps an in-game season for the session.
uint32_t offlineWeatherDay=0;
void updateLocalWeather(){
  if(view.game.running())return;
  static uint32_t readAt=0,day=0;static int month=0;
  uint32_t now=millis();
  if(!month || now-readAt>=1000){
    time_t clock=time(nullptr);
    if(clock<1735689600)clock=1735689600+time_t(offlineWeatherDay)*86400+now/1000;
    clock+=7*3600;
    const tm* bangkok=gmtime(&clock);
    if(bangkok){month=bangkok->tm_mon+1;day=uint32_t(clock/86400);}
    readAt=now;
  }
  view.game.updateWeather(month,day);
}
Page returnTo=Page::Play;
RumblePlan haptics;
ReelDetents detents;
uint32_t audition=0,lastDirection=0;
bool auditioning=false, wasHapticPlay=false;
template<int N> struct OriginalBook {Entry entries[N];uint8_t rank[3],reserved;};
static_assert(sizeof(OriginalBook<52>)==420,"The released NVS schema must remain readable");
bool saveBook(){
  OriginalBook<originalSpecies> old{};
  std::copy_n(view.game.progress.book.entries,originalSpecies,old.entries);
  std::copy_n(view.game.progress.rank,3,old.rank);
  view.saveFailed=store.putBytes("atlas-3",&old,sizeof(old))!=sizeof(old);
  return !view.saveFailed;
}
template<int N> bool loadOriginalBook(const char* key){
  OriginalBook<N> old;
  if(store.getBytesLength(key)!=sizeof(old) || store.getBytes(key,&old,sizeof(old))!=sizeof(old))return false;
  std::copy_n(old.entries,N,view.game.progress.book.entries);std::copy_n(old.rank,3,view.game.progress.rank);
  return true;
}
void togglePractice(){view.practice=!view.practice;view.game.enter(Phase::Ready);}
void setCueLevel(){view.sound.cueVolume=(view.sound.cueVolume+1)%4;store.putUChar("cuevol",view.sound.cueVolume);}


struct HeldFish {int fish,length,prior;};
void restore(){
  store.begin("willow-v1",false);
  if(store.getBytesLength("poses")==sizeof(Calibration))store.getBytes("poses",&setupPose,sizeof(setupPose));
  view.calibrated=setupPose.valid();
  if(!loadOriginalBook<originalSpecies>("atlas-3") && loadOriginalBook<40>("atlas-2"))saveBook();
  if(!restoreExtraBook(view.game.progress.book))view.saveFailed=true;
  view.game.weatherMode=store.getUChar("weather",0)%5;
  view.timeMode=store.getUChar("time-mode",4)%5;view.rodFinish=store.getUChar("finish",0)%3;
  view.game.setBait(store.getUChar("bait",0));
  view.game.setRig(store.getUChar("rig",0)%3);
  view.game.timeSlot=view.timeMode<4?view.timeMode:0;
  view.destination=store.getUChar("spot",store.getUChar("water",0)%4)%destinationCount;view.game.site=destinations[view.destination].pool;view.sound.arrangement=view.destination;
  view.game.destination=view.destination;
  HeldFish pending{};
  if(store.getBytesLength("held-fish")==sizeof(pending) && store.getBytes("held-fish",&pending,sizeof(pending))==sizeof(pending) &&
     validSavedSize(pending.fish,pending.length) &&
     int(view.game.progress.book.entries[pending.fish].count)==pending.prior){
    view.game.fish=pending.fish;view.game.length=pending.length;view.game.filed=false;view.game.enter(Phase::Landed);
  }
  view.rumble=store.getUChar("rumble",0)%4;
  view.page=view.calibrated?Page::Play:Page::Rest;
  view.sound.music=store.getUChar("music",0);view.sound.volume=store.getUChar("volume",2);
  view.sound.cue=store.getUChar("cue",0);view.sound.cueVolume=store.getUChar("cuevol",2);
  view.sound.reelVolume=store.getUChar("reel-vol",1)%4;
  view.sound.reverse=store.getBool("reverse",false);
  if(!view.sound.valid())view.sound=SoundSettings{};view.sound.site=view.game.site%4;
}
void playPage(){
  view.page=(view.practice||view.calibrated)?Page::Play:Page::Rest;
  rod=Gesture{};wheel.previous=-1;
}
void change(int x,int y,bool& practiceTap){
  if(view.page==Page::Arrival){playPage();return;}
  if(view.page==Page::TouchCheck){
    if(x>=52&&x<=152&&y>=283){view.page=Page::Bench;return;}
    view.lastTouchX=x;view.lastTouchY=y;
    if(view.touchStep<9&&std::abs(x-touchColumn[view.touchStep%3])<=12&&
       std::abs(y-touchRow[view.touchStep/3])<=12)++view.touchStep;
    Serial.printf("touch x=%d y=%d accepted=%d/9\n",x,y,int(view.touchStep));
    return;
  }
  if(view.page==Page::Play && view.game.phase==Phase::Landed){
    auto& game=view.game;
    const int id=game.fish;
    const Entry before=game.progress.book.entries[id];
    if(game.fileCatch()){
      const bool saved=id<originalSpecies?saveBook():saveExtraEntry(id,game.progress.book.entries[id]);
      view.saveFailed=!saved;
      if(saved)eventCatch(view.destination,id,game.length,landedDay);
      else{
        game.progress.book.entries[id]=before;game.filed=false;
        game.newEntry=false;game.personalBest=false;game.pointsAwarded=0;
      }
    }
    return;
  }
  if((view.page==Page::Play||view.page==Page::Rest||view.page==Page::Raise) && y<40 && x>=365){
    returnTo=view.page;view.page=Page::Hub;rod=Gesture{};stopRumble();return;
  }
  if(menuui::overlay(view.page)){
    if(!menuui::inside(x,y)){
      if(view.page==Page::Network)stopPairing();
      auditioning=false;stopRumble();view.page=returnTo;
      if(view.page==Page::Play)playPage();
      return;
    }
    x-=menuui::x;y-=menuui::y;
    if(y<menuui::header){
      if(view.page==Page::Journey && x>=150&&x<304){view.page=Page::Bait;return;}
      if(view.page==Page::Bait && x>=menuui::w-80){view.page=Page::Journey;return;}
      if(view.page==Page::Waters && x>=130 && x<303){view.pendingWeather=(view.pendingWeather+1)%5;return;}
      if(x>=menuui::w-80){
        if(view.page==Page::Network)stopPairing();
        auditioning=false;stopRumble();
        view.page=view.page==Page::Hub?returnTo:Page::Hub;
        if(view.page==Page::Play)playPage();
      }
      return;
    }
  }
  if(view.page==Page::Bait){
    if(view.game.running()||view.game.phase==Phase::Landed)return;
    int choice=view.game.bait;
    if(y>=38&&y<38+6*27)choice=6*(choice/6)+(y-38)/27;
    else if(y>=210&&y<252)choice=6*std::min(2,x*3/menuui::w)+choice%6;
    if(choice!=view.game.bait && view.game.setBait(choice))store.putUChar("bait",choice);
    return;
  }
  if(view.page==Page::Hub){
    switch((y-menuui::header)/menuui::hubRow){
    case 0:view.pendingSite=view.destination;view.spotPage=view.destination/4;view.pendingTime=view.timeMode;view.pendingWeather=view.game.weatherMode;view.page=Page::Waters;break;
    case 1:view.page=Page::Book;view.bookWater=view.game.site;view.bookPage=0;view.bookFilter=BookFilter::Nearby;break;
    case 2:view.page=Page::Journey;view.notice="First find earns 1 point, then every 3 new species.";view.refundConfirm=false;break;
    case 3:if(!view.driver)view.driver=initRumble();view.page=Page::Bench;view.casts=view.lifts=0;view.turns=0;view.direction=0;view.benchEvent="Hold in playing position";rod=Gesture{};wheel.previous=-1;break;
    case 4:view.page=Page::Options;break;
    case 5:togglePractice();playPage();break;
    case 6:view.page=Page::Network;break;
    }return;
  }
  if(view.page==Page::Bench && y<40 && x>=365){view.page=Page::Hub;auditioning=false;stopRumble();return;}
  if(view.page==Page::Network){
    if(y>=138 && y<169)startPairing();
    else if(y>=169&&y<200)checkUpdate();
    else if(y>=200&&y<231)toggleRadio();
    else if(y>=231&&y<262)toggleEvent();
    return;
  }
  if(view.page==Page::Waters){
    if(y<menuui::header+4*menuui::waterRow){
      int id=view.spotPage*4+(y-menuui::header)/menuui::waterRow;
      if(id<destinationCount)view.pendingSite=id;
    }
    else if(y>=menuui::periodY&&y<menuui::periodY+29)view.pendingTime=5*x/menuui::w;
    else if(y>=menuui::travelY&&y<menuui::travelY+32){
      if(x<menuui::w/4||x>=3*menuui::w/4){int pages=(destinationCount+3)/4;view.spotPage=(view.spotPage+(x<menuui::w/4?pages-1:1))%pages;return;}
      const bool travelling=view.pendingSite!=view.destination;
      if(travelling||view.pendingTime!=view.timeMode||view.pendingWeather!=view.game.weatherMode)view.game.enter(Phase::Ready);
      view.destination=view.pendingSite;view.game.site=destinations[view.destination].pool;view.sound.site=view.game.site%4;view.sound.arrangement=view.destination;view.timeMode=view.pendingTime;
      view.game.arriveAt(view.destination);

      view.game.weatherMode=view.pendingWeather;store.putUChar("weather",view.pendingWeather);
      store.putUChar("spot",view.destination);store.putUChar("time-mode",view.timeMode);
      view.game.timeSlot=view.timeMode==4?pondPeriod():view.timeMode;playPage();
      if(travelling){view.arrivalStart=view.time;view.page=Page::Arrival;}
    }return;
  }
  if(view.page==Page::Book){
    if(y<56){
      view.bookWater=(view.bookWater+1)%siteCount;view.bookPage=0;view.bookFilter=BookFilter::All;
    }else if(y>=menuui::bookNav && y<menuui::bookNav+33){
      if(x>=menuui::w/4 && x<3*menuui::w/4){
        view.bookFilter=BookFilter((int(view.bookFilter)+1)%3);view.bookPage=0;
        if(view.bookFilter==BookFilter::Nearby)view.bookWater=view.game.site;
      }else{
        const int entries=view.game.progress.book.waterCount(view.bookWater,view.destination,view.bookFilter);
        const int pages=std::max(1,(entries+menuui::bookRows-1)/menuui::bookRows);
        view.bookPage=(view.bookPage+(x<menuui::w/4?pages-1:1))%pages;
      }
    }
    return;
  }
  if(view.page==Page::Journey){
    if(y>=menuui::rigY&&y<menuui::rigY+23){
      if(view.game.running()){view.notice="Finish this cast to change technique.";return;}
      view.game.setRig((int(view.game.rig)+1)%3);store.putUChar("rig",int(view.game.rig));
      view.notice="Technique fitted.";return;
    }
    if(y>=menuui::upgradeY&&y<menuui::upgradeY+3*menuui::upgradeRow){int i=(y-menuui::upgradeY)/menuui::upgradeRow;view.refundConfirm=false;
      if(view.game.progress.upgrade(i)){
        if(saveBook())view.notice="Upgrade fitted.";
        else{--view.game.progress.rank[i];view.notice="Save failed. Try the upgrade again.";}
      }
      else view.notice=view.game.progress.rank[i]>=3?"Maximum rank.":view.game.progress.rank[i]>=view.game.progress.chapter()?"Advance the story to open this rank.":"Discover more species to earn points.";
    } else if(y>=menuui::finishY&&y<menuui::finishY+37&&x<menuui::w/2){view.rodFinish=(view.rodFinish+1)%3;store.putUChar("finish",view.rodFinish);view.refundConfirm=false;}
    else if(y>=menuui::finishY&&y<menuui::finishY+37){if(view.refundConfirm){view.game.progress.retrain();saveBook();view.notice="Points returned. Choose a new setup.";}view.refundConfirm=!view.refundConfirm;}return;
  }
  if(view.page==Page::Bench){
    if(y>=300&&x>=270){view.page=Page::TouchCheck;view.touchStep=0;view.lastTouchX=view.lastTouchY=-1;stopRumble();return;}
    if(y>=166&&y<197){view.sound.reverse=!view.sound.reverse;store.putBool("reverse",view.sound.reverse);view.turns=0;view.direction=0;wheel.previous=-1;}
    else if(y>=197&&y<233){if(x<233)setCueLevel();else{auditioning=true;audition=millis();SoundSettings sample=view.sound;sample.cue=0;setSound(sample,false,true);}}
    else if(y>=233&&y<274){if(x<157){view.rumble=(view.rumble+1)%4;store.putUChar("rumble",view.rumble);stopRumble();}
      else {Pulse test=x<266?Pulse::Tease:x<368?Pulse::Bite:Pulse::Pull;detents.feedback(0,test,millis());view.driver=driveRumble(test,view.rumble,.8f);view.benchEvent=!view.driver?"Driver absent":!view.rumble?"Rumble off":test==Pulse::Tease?"Tease audition":test==Pulse::Bite?"Bite audition":"Pull audition";}}
    else if(y>=274&&y<300){
      Pulse sample=x<160?Pulse::PickSample:x<320?Pulse::Bottom:Pulse::Dash;
      detents.feedback(0,sample,millis());
      view.driver=driveRumble(sample,view.rumble,.4f);
      view.benchEvent=!view.driver?"Driver absent":!view.rumble?"Rumble off":
        sample==Pulse::PickSample?"Prawn picking bait":sample==Pulse::Bottom?"Bottom hold":"Fast run";
    }
    return;
  }
  if(view.page==Page::Options){
    if(y>=menuui::header+8*menuui::optionRow)return;
    bool preview=false;
    switch((y-menuui::header)/menuui::optionRow){
    case 0:view.sound.music=(view.sound.music+1)%4;store.putUChar("music",view.sound.music);break;
    case 1:view.sound.volume=(view.sound.volume+1)%4;store.putUChar("volume",view.sound.volume);break;
    case 2:view.sound.cue=(view.sound.cue+1)%3;store.putUChar("cue",view.sound.cue);preview=true;break;
    case 3:setCueLevel();preview=true;break;
    case 4:view.sound.reverse=!view.sound.reverse;store.putBool("reverse",view.sound.reverse);wheel.previous=-1;break;
    case 5:view.practice=!view.practice;view.game.enter(Phase::Ready);playPage();return;
    case 6:view.practice=false;view.page=Page::Rest;view.badPose=false;rod=Gesture{};return;
    case 7:view.sound.reelVolume=(view.sound.reelVolume+1)%4;store.putUChar("reel-vol",view.sound.reelVolume);break;
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
  if(view.page==Page::Play && !view.game.running() && y>=141 && y<=299){
    view.game.setAim(x/480.f,y/320.f);
    if(view.practice)practiceTap=true;
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
  Serial.begin(115200);restore();view.game.beginSession(esp_random());view.game.arriveAt(view.destination);offlineWeatherDay=view.game.seed%365;updateLocalWeather();beginBoard();view.battery=readBattery();beginConnected();view.driver=initRumble();beginScene();
  view.audio=startSound();setSound(view.sound,false,false);
  Serial.printf("Thai Waters 0.8 | LCD %d IMU %d audio %d charge config 4.20V/300mA readback %d\n",screenOK,imuOK,view.audio,powerOK);
  lastTick=millis();paint(view);confirmUpdateHealth(screenOK && imuOK && powerOK && view.audio);
}
void loop(){
  uint32_t now=millis(),dt=now-lastTick;
  if(dt<12){delay(1);return;}
  lastTick=now;dt=std::min<uint32_t>(dt,100);view.time=now;
  if(now-lastBattery>=3000){view.battery=readBattery();lastBattery=now;}
  tickConnected();eventTick(view.destination);
  if(view.timeMode==4 && !view.game.running())view.game.timeSlot=pondPeriod();
  updateLocalWeather();
  const bool wasArriving=view.page==Page::Arrival;
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
  if(view.page==Page::Arrival && now-view.arrivalStart>=arrival::duration)playPage();
  Phase before=view.game.phase;
  if(!wasArriving && view.page==Page::Play && (view.practice||(view.motion&&view.field==Field::Good))){
    view.game.rodHeldHigh=!view.practice && rod.high;
    view.game.tick(dt,view.practice?tap:rod.cast,view.practice?tap:rod.rise,view.practice?(tap?(view.game.phase==Phase::Snag&&view.game.contact==2?-.19f:.25f):0):turns);
  } else if(view.page==Page::Play)rod=Gesture{};
  if(view.game.phase!=before){
    Serial.printf("phase=%u catch=%d line=%.2f\n",unsigned(view.game.phase),view.game.catches,view.game.line);
  }
  LandingCue landing;
  if(before!=view.game.phase && view.game.phase==Phase::Landed){
    landing={catalog[view.game.fish].tier,view.game.landingReward()};
    landedDay=eventDay();
    HeldFish heldFish{view.game.fish,view.game.length,int(view.game.progress.book.entries[view.game.fish].count)};
    store.putBytes("held-fish",&heldFish,sizeof(heldFish));
  }
  bool active=!wasArriving && view.page==Page::Play && (view.practice||(view.motion&&view.field==Field::Good));
  if(wasHapticPlay&&!active)stopRumble();
  wasHapticPlay=active;
  Pulse pulse=haptics.tick(view.game,now,active);
  // Only measured rotation produces clicks, including in practice mode.
  bool reelActive=(active || view.page==Page::Bench) && view.field==Field::Good;
  int click=0;
  if(reelActive)click=detents.feedback(detents.measure(turns),pulse,now);
  else detents=ReelDetents{};
  if(pulse!=Pulse::None)view.driver=driveRumble(pulse,view.rumble,view.game.heat);
  else if(click)view.driver=driveRumble(Pulse::Detent,view.rumble,0);
  if(auditioning && now-audition>=420)auditioning=false;
  SoundSettings mix=view.sound;if(auditioning)mix.cue=0;
  setSound(mix,active && view.game.phase==Phase::Fight,view.game.phase!=before&&view.game.phase==Phase::Bite,click,landing);
  if(!everDrawn||now-lastDraw>=55){lastDraw=now;everDrawn=true;paint(view);}
}


