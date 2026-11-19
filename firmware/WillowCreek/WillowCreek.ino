#include "Scene.h"
#include "Arrival.h"
#include "CatchLog.h"
#include "Rumble.h"
#include "ReelDetents.h"
#include "Connected.h"
#include "RodController.h"
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
CatchTransaction catchTx;
bool journalLocked=false,heldDirty=false;
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
bool writeTransaction(const CatchTransaction& next){
  if(journalLocked || store.putBytes("catch-tx1",&next,sizeof(next))!=sizeof(next))return false;
  CatchTransaction check;
  if(store.getBytes("catch-tx1",&check,sizeof(check))!=sizeof(check) || memcmp(&check,&next,sizeof(check)))return false;
  catchTx=next;heldDirty=false;return true;
}
void holdLanding(bool legacy){
  auto& g=view.game;
  if(journalLocked || catchTx.stage!=CatchStage::Idle || catchTx.record.sequence==UINT32_MAX){view.saveFailed=true;return;}
  const uint32_t sequence=catchTx.record.sequence+1;
  catchTx={};catchTx.stage=CatchStage::Landed;
  auto& r=catchTx.record;
  r.sequence=sequence;r.species=g.fish;r.cm=g.length;r.grams=g.landedGrams;r.measurement=archivedMeasure(g.fish,g.length);
  catchTx.priorCount=g.progress.book.entries[g.fish].count;catchTx.priorBest=g.progress.book.entries[g.fish].best;
  if(legacy)r.flags=LegacyPending;
  else{
    r.spot=view.destination;r.weather=uint8_t(g.weather);r.period=g.timeSlot;r.bait=g.bait;
    r.utc=pondUtc();r.flags=r.utc?TimeKnown:0;r.cupDay=landedDay;
  }
  heldDirty=true;view.saveFailed=!writeTransaction(catchTx);
}
bool finishLanding(){
  auto& g=view.game;
  if(journalLocked || catchTx.stage==CatchStage::Idle || (heldDirty && !writeTransaction(catchTx)))return false;
  if(catchTx.stage==CatchStage::Landed){
    CatchTransaction ack=catchTx;
    if(ack.record.species>=originalSpecies){
      if(journalDrive(true)!=DiskRead::Good)return false;
      JournalSector sector;int slot;
      const auto prior=loadSector((ack.record.species-originalSpecies)/journalPageEntries,sector,slot);
      if(prior==DiskRead::Invalid)return false;
      ack.emptyExtraPage=prior==DiskRead::Missing;
    }
    ack.stage=CatchStage::Acknowledged;
    if(!writeTransaction(ack))return false;
  }
  const CatchTransaction tx=catchTx;
  auto& e=g.progress.book.entries[tx.record.species];
  const auto write=[&](const Entry& target){
    const Entry prior=e;e=target;
    const bool ok=tx.record.species<originalSpecies?saveBook():saveExtraEntry(tx.record.species,target,tx.emptyExtraPage);
    if(!ok)e=prior;
    return ok;
  };
  if(!commitCatch(tx,e,write,writeTransaction))return false;
  // Use the recorded pre-catch values for the reward animation even on replay.
  e.count=tx.priorCount;e.best=tx.priorBest;
  g.fileCatch();
  if(tx.record.spot!=255)eventCatch(tx.record.spot,tx.record.species,tx.record.cm,tx.record.cupDay);
  return true;
}
void showHeldCatch(){
  const auto& r=catchTx.record;auto& g=view.game;
  g.fish=r.species;g.length=r.cm;g.filed=false;g.emptyCast=false;g.enter(Phase::Landed);g.landedGrams=r.grams;
  if(r.spot!=255){view.destination=g.destination=r.spot;g.site=destinations[r.spot].pool;}
}
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
  const size_t txSize=store.getBytesLength("catch-tx1");
  if(txSize){
    if(txSize!=sizeof(catchTx) || store.getBytes("catch-tx1",&catchTx,sizeof(catchTx))!=sizeof(catchTx) || !legalTransaction(catchTx)){
      journalLocked=view.saveFailed=true;
    }else if(catchTx.stage!=CatchStage::Idle){
      showHeldCatch();
      if(catchTx.stage==CatchStage::Acknowledged)view.saveFailed=!finishLanding();
    }
  }else if(store.getBytesLength("held-fish")==sizeof(pending) && store.getBytes("held-fish",&pending,sizeof(pending))==sizeof(pending) &&
     validSavedSize(pending.fish,pending.length) &&
     int(view.game.progress.book.entries[pending.fish].count)==pending.prior){
    view.game.fish=pending.fish;view.game.length=pending.length;view.game.filed=false;view.game.enter(Phase::Landed);holdLanding(true);
  }
  view.rumble=store.getUChar("rumble",0)%4;
  view.page=view.calibrated || view.game.phase==Phase::Landed?Page::Play:Page::Rest;
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
void showHistory(uint32_t sequence){
  view.page=Page::CatchHistory;
  view.historyCount=catchTx.record.sequence-(catchTx.stage!=CatchStage::Idle && catchTx.record.sequence?1u:0u);
  view.history={};view.historyError=journalLocked;
  if(!view.historyCount || view.historyError)return;
  if(!sequence || sequence>view.historyCount)sequence=view.historyCount;
  view.historyError=!readCatch(sequence,view.history);
}
void change(int x,int y,bool& practiceTap){
  if(view.page==Page::Arrival){playPage();return;}
  if(view.page==Page::TouchCheck){
    if(x>=52&&x<=152&&y>=270){view.page=Page::Bench;return;}
    view.lastTouchX=x;view.lastTouchY=y;
    if(view.touchStep<9&&std::abs(x-touchColumn[view.touchStep%3])<=12&&
       std::abs(y-touchRow[view.touchStep/3])<=12)++view.touchStep;
    Serial.printf("touch x=%d y=%d accepted=%d/9\n",x,y,int(view.touchStep));
    return;
  }
  if(view.page==Page::Play && view.game.phase==Phase::Landed){
    if(!view.game.filed)view.saveFailed=!finishLanding();
    return;
  }
  if(view.page==Page::Play && x<111 && y<52){returnTo=view.page;view.page=Page::Journey;rod=Gesture{};stopRumble();return;}
  if((view.page==Page::Play||view.page==Page::Rest||view.page==Page::Raise) && y<52 && x>=395){
    returnTo=view.page;view.page=Page::Hub;rod=Gesture{};stopRumble();return;
  }
  if(menuui::overlay(view.page)){
    if(!menuui::inside(x,y)){
      if(view.page==Page::Network)stopPairing();
      if(view.page==Page::Controller)endRodController();
      auditioning=false;stopRumble();view.page=returnTo;
      if(view.page==Page::Play)playPage();
      return;
    }
    x-=menuui::x;y-=menuui::y;
    if(y<menuui::header){
      if(view.page==Page::Journey && x>=150&&x<304){view.page=Page::Bait;return;}
      if(view.page==Page::Bait && x>=menuui::w-80){view.page=Page::Journey;return;}
      if(view.page==Page::Waters && x>=130 && x<303){view.pendingWeather=(view.pendingWeather+1)%5;return;}
      if(view.page==Page::Book && x>=148 && x<304){view.bookWater=(view.bookWater+1)%(siteCount+1);view.bookPage=0;view.bookFilter=BookFilter::All;return;}
      if(x>=menuui::w-80){
        if(view.page==Page::BookDetail || view.page==Page::CatchHistory){view.page=Page::Book;return;}
        if(view.page==Page::Network)stopPairing();
      if(view.page==Page::Controller)endRodController();
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
    int index=menuui::gridIndex(x,y,menuui::gridTop,menuui::baitRow,6);
    if(index>=0)choice=6*(choice/6)+index;
    else if(y>=menuui::depthY)choice=6*std::min(2,x*3/menuui::w)+choice%6;
    if(choice!=view.game.bait && view.game.setBait(choice))store.putUChar("bait",choice);
    return;
  }
  if(view.page==Page::Hub){
    switch(menuui::gridIndex(x,y,menuui::gridTop,menuui::gridRow,7)){
    case 0:view.pendingSite=view.destination;view.spotPage=view.destination/4;view.pendingTime=view.timeMode;view.pendingWeather=view.game.weatherMode;view.page=Page::Waters;break;
    case 1:view.page=Page::Book;view.bookWater=siteCount;view.bookPage=0;view.bookFilter=BookFilter::All;break;
    case 2:view.page=Page::Journey;view.notice="First find earns 1 point, then every 3 new species.";view.refundConfirm=false;break;
    case 3:if(!view.driver)view.driver=initRumble();view.page=Page::Bench;view.casts=view.lifts=0;view.turns=0;view.direction=0;view.benchEvent="Hold in playing position";rod=Gesture{};wheel.previous=-1;break;
    case 4:view.page=Page::Options;break;
    case 5:togglePractice();playPage();break;
    case 6:view.page=Page::Network;break;
    }return;
  }
  if(view.page==Page::Bench && y<52 && x>=395){view.page=Page::Hub;auditioning=false;stopRumble();return;}
  if(view.page==Page::Network){
    const int action=menuui::gridIndex(x,y,menuui::networkTop,menuui::networkRow,5);
    if(action==0)startPairing();
    else if(action==1)checkUpdate();
    else if(action==2)toggleRadio();
    else if(action==3)toggleEvent();
    else if(action==4){
      stopPairing();view.page=Page::Controller;rod=Gesture{};wheel.previous=-1;
      beginRodController(view.battery.percent);
    }
    return;
  }
  if(view.page==Page::Controller){
    const int action=menuui::gridIndex(x,y,menuui::controllerTop,menuui::controllerRow,2);
    if(action==0){armRodController();rod=Gesture{};wheel.previous=-1;}
    if(action==1){endRodController();view.page=Page::Network;}
    return;
  }
  if(view.page==Page::Waters){
    int index=menuui::gridIndex(x,y,menuui::gridTop,menuui::waterRow,4);
    if(index>=0){
      int id=view.spotPage*4+index;
      if(id<destinationCount)view.pendingSite=id;
    }
    else if(y>=menuui::periodY&&y<menuui::travelY)view.pendingTime=5*x/menuui::w;
    else if(y>=menuui::travelY){
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
    if(y>=menuui::bookNav){
      if(x>=menuui::w/2 && x<3*menuui::w/4){showHistory(0);return;}
      if(x>=menuui::w/4 && x<menuui::w/2){
        view.bookFilter=BookFilter((int(view.bookFilter)+1)%3);view.bookPage=0;
        view.bookWater=view.bookFilter==BookFilter::Nearby?view.game.site:siteCount;
      }else{
        const int entries=view.game.progress.book.waterCount(view.bookWater,view.destination,view.bookFilter);
        const int pages=std::max(1,(entries+menuui::bookRows-1)/menuui::bookRows);
        view.bookPage=(view.bookPage+(x<menuui::w/4?pages-1:1))%pages;
      }
    }else{
      int tile=menuui::gridIndex(x,y,menuui::gridTop,86,4);
      if(tile>=0){view.bookSpecies=bookTile(view,tile);if(view.bookSpecies>=0)view.page=Page::BookDetail;}
    }
    return;
  }
  if(view.page==Page::BookDetail)return;
  if(view.page==Page::CatchHistory){
    if(y>=menuui::bookNav && view.historyCount){
      const uint32_t current=view.history.sequence;
      if(x<menuui::w/2)showHistory(current>1?current-1:1);
      else showHistory(current<view.historyCount?current+1:view.historyCount);
    }
    return;
  }
  if(view.page==Page::Journey){
    int action=menuui::gridIndex(x,y,menuui::workshopTop,menuui::workshopRow,6);
    if(action==0){
      if(view.game.running()){view.notice="Finish this cast to change technique.";return;}
      view.game.setRig((int(view.game.rig)+1)%3);store.putUChar("rig",int(view.game.rig));
      view.notice="Technique fitted.";return;
    }
    if(action>=2&&action<=4){int i=action-2;view.refundConfirm=false;
      if(view.game.progress.upgrade(i)){
        if(saveBook())view.notice="Upgrade fitted.";
        else{--view.game.progress.rank[i];view.notice="Save failed. Try the upgrade again.";}
      }
      else view.notice=view.game.progress.rank[i]>=3?"Maximum rank.":view.game.progress.rank[i]>=view.game.progress.chapter()?"Advance the story to open this rank.":"Discover more species to earn points.";
    } else if(action==1){view.rodFinish=(view.rodFinish+1)%3;store.putUChar("finish",view.rodFinish);view.refundConfirm=false;}
    else if(action==5){if(view.refundConfirm){view.game.progress.retrain();saveBook();view.notice="Points returned. Choose a new setup.";}view.refundConfirm=!view.refundConfirm;}return;
  }
  if(view.page==Page::Bench){
    int action=menuui::benchAction(x,y);
    if(action==11){view.page=Page::TouchCheck;view.touchStep=0;view.lastTouchX=view.lastTouchY=-1;stopRumble();return;}
    if(action==0){view.sound.reverse=!view.sound.reverse;store.putBool("reverse",view.sound.reverse);view.turns=0;view.direction=0;wheel.previous=-1;}
    else if(action==1)setCueLevel();
    else if(action==2){auditioning=true;audition=millis();SoundSettings sample=view.sound;sample.cue=0;setSound(sample,false,true);}
    else if(action==3){view.rumble=(view.rumble+1)%4;store.putUChar("rumble",view.rumble);stopRumble();}
    else if(action>=4&&action<=6){
      Pulse test=action==4?Pulse::Tease:action==5?Pulse::Bite:Pulse::Pull;detents.feedback(0,test,millis());view.driver=driveRumble(test,view.rumble,.8f);view.benchEvent=!view.driver?"Driver absent":!view.rumble?"Rumble off":test==Pulse::Tease?"Tease audition":test==Pulse::Bite?"Bite audition":"Pull audition";
    }
    else if(action>=8&&action<=10){
      Pulse sample=action==8?Pulse::PickSample:action==9?Pulse::Bottom:Pulse::Dash;
      detents.feedback(0,sample,millis());
      view.driver=driveRumble(sample,view.rumble,.4f);
      view.benchEvent=!view.driver?"Driver absent":!view.rumble?"Rumble off":
        sample==Pulse::PickSample?"Prawn picking bait":sample==Pulse::Bottom?"Bottom hold":"Fast run";
    }
    return;
  }
  if(view.page==Page::Options){
    bool preview=false;
    switch(menuui::gridIndex(x,y,menuui::gridTop,menuui::gridRow,8)){
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
  if(((view.page==Page::Play && !view.practice)||view.page==Page::Bench||view.page==Page::Controller) && view.calibrated){
    view.degrees=setupPose.tilt(filtered);view.span=setupPose.span();
    rod.sample(view.degrees,view.span,now);view.raised=rod.high;
  } else {rod=Gesture{};view.raised=false;}
}
}
void printCatchRecord(uint32_t index){
  const uint32_t last=catchTx.record.sequence-(catchTx.stage!=CatchStage::Idle && catchTx.record.sequence?1u:0u);
  if(journalLocked){Serial.println("{\"ok\":false,\"error\":\"unreadable transaction\"}");return;}
  if(!index){Serial.printf("{\"schema\":1,\"count\":%lu}\n",(unsigned long)last);return;}
  CatchRecord r;
  if(index>last || !readCatch(index,r)){Serial.println("{\"ok\":false}");return;}
  Serial.printf("{\"seq\":%lu,\"species\":%u,\"cm\":%u,\"measure\":\"%s\",\"grams\":%lu,\"time_valid\":%s,\"utc\":%lu,\"spot\":%u,\"weather\":%u,\"period\":%u,\"bait\":%u,\"legacy\":%s}\n",
    (unsigned long)index,r.species,r.cm,archivedMeasures[r.measurement],(unsigned long)r.grams,(r.flags&TimeKnown)?"true":"false",
    (unsigned long)r.utc,r.spot,r.weather,r.period,r.bait,(r.flags&LegacyPending)?"true":"false");
}
void setup(){
  Serial.begin(115200);restore();view.game.beginSession(esp_random());view.game.arriveAt(view.destination);offlineWeatherDay=view.game.seed%365;updateLocalWeather();beginBoard();view.battery=readBattery();beginConnected();view.driver=initRumble();beginScene();
  view.audio=startSound();setSound(view.sound,false,false);
  Serial.printf("Thai Waters 0.9.2 controller preview | LCD %d IMU %d audio %d charge config 4.20V/300mA readback %d | CHGLED Type A readback %d\n",screenOK,imuOK,view.audio,powerOK,chargeLampOK);
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
  const bool controller=view.page==Page::Controller;
  const bool validTilt=controller && view.calibrated && view.motion && view.accelG>=.82f && view.accelG<=1.19f;
  tickRodController(now,controller&&rod.cast,controller&&rod.rise,controller?turns:0,validTilt?view.degrees/view.span:NAN,view.battery.percent);
  if(view.page==Page::Arrival && now-view.arrivalStart>=arrival::duration)playPage();
  Phase before=view.game.phase;
  view.game.soundEdges=0;
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
    holdLanding(false);
  }
  bool active=!wasArriving && view.page==Page::Play && (view.practice||(view.motion&&view.field==Field::Good));
  if(wasHapticPlay&&!active)stopRumble();
  wasHapticPlay=active;
  Pulse pulse=haptics.tick(view.game,now,active);
  // Only measured rotation produces clicks, including in practice mode.
  bool reelActive=(active || view.page==Page::Bench || (controller&&rodControllerStreaming())) && view.field==Field::Good;
  int click=0;
  if(reelActive)click=detents.feedback(detents.measure(turns),pulse,now);
  else detents=ReelDetents{};
  if(pulse!=Pulse::None)view.driver=driveRumble(pulse,view.rumble,view.game.heat);
  else if(click)view.driver=driveRumble(Pulse::Detent,view.rumble,0);
  if(auditioning && now-audition>=420)auditioning=false;
  SoundSettings mix=view.sound;if(controller)mix.music=3;if(auditioning)mix.cue=0;
  setSound(mix,active && view.game.phase==Phase::Fight,view.game.phase!=before&&view.game.phase==Phase::Bite,click,landing,view.game.soundEdges);
  if(!everDrawn||now-lastDraw>=(controller?320u:55u)){lastDraw=now;everDrawn=true;paint(view);}
}


