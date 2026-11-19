#include "../WillowCreek/WillowCreek.ino"
#include <cassert>
#include <cstdio>
namespace creek {
std::map<std::string,std::vector<uint8_t>> diskPages;
bool diskWriteOK=true;
DiskRead journalDrive(bool){return DiskRead::Good;}
DiskRead journalDiskRead(const char* path,void* dst,size_t size){
 auto file=diskPages.find(path);if(file==diskPages.end())return DiskRead::Missing;
 if(file->second.size()!=size)return DiskRead::Invalid;
 memcpy(dst,file->second.data(),size);return DiskRead::Good;
}
bool journalDiskWrite(const char* path,const void* src,size_t size){
 if(!diskWriteOK)return false;
 const auto* first=static_cast<const uint8_t*>(src);
 if(testPersistentWrite){
   diskPages[path]={first,first+size/2};
   testPersistentWrite(path,false);
 }
 diskPages[path]={first,first+size};
 if(testPersistentWrite)testPersistentWrite(path,true);
 return true;
}
}
uint32_t testClock=0;Arduino_Canvas screen;bool screenOK=true,imuOK=true,powerOK=true,chargeLampOK=true;
creek::Vec inputG{0,0,1};int encoder=4070,px=0,py=0,cuePulses=0,motorPulses=0;
bool touched=false;Field magnet=Field::Good;SoundSettings lastMix;
BatteryReading readBattery(){return batteryFromStatus(0x28,0x20,57);}
void beginBoard(){} bool acceleration(creek::Vec& v){v=inputG;return true;}
Field readWheel(int& a){a=encoder;return magnet;}
bool touchPoint(int& x,int& y){x=px;y=py;return touched;}
void beginScene(){}void paint(const View&){}
int landingPulses=0;LandingCue heardLanding;
bool startSound(){return true;}
void setSound(const SoundSettings& s,bool,bool cue,int,LandingCue landing,uint8_t){
 lastMix=s;if(cue)++cuePulses;
 if(landing.active()){++landingPulses;heardLanding=landing;}
}
bool initRumble(){return true;}bool driveRumble(Pulse p,uint8_t level,float){if(p!=Pulse::None && level)++motorPulses;return true;}void stopRumble(){}
void beginConnected(){}void tickConnected(){}void startPairing(){}void stopPairing(){}void toggleRadio(){}void checkUpdate(){}int pondPeriod(){return 1;}
uint32_t fakeUtc=0;
uint32_t pondUtc(){return fakeUtc;}
bool controllerOpen=false,controllerArmed=false;
bool beginRodController(int){controllerOpen=true;return true;}
void endRodController(){controllerOpen=controllerArmed=false;}
bool rodControllerStreaming(){return controllerArmed;}
void armRodController(){controllerArmed=controllerOpen&&!controllerArmed;}
void tickRodController(uint32_t,bool,bool,float,float,int){}
void confirmUpdateHealth(bool){}void eventTick(int){}void eventCatch(int,int,int,unsigned){}unsigned eventDay(){return 0;}const char* cupGoal(){return "";}const char* cupBait(){return "";}const char* cupStanding(){return "";}void toggleEvent(){}
void step(int count){while(count--){testClock+=16;loop();}}
void tap(int x,int y){px=x;py=y;touched=true;step(3);touched=false;step(4);}
void gridTap(int index,int top=menuui::gridTop,int row=menuui::gridRow){
 tap(menuui::x+menuui::w/4+(index%2)*menuui::w/2,menuui::y+top+(index/2)*row+row/2);
}
int writesLeft=0;
void cutPower(const char*,bool){if(!--writesLeft)throw 1;}
void restartJournal(){
 view={};catchTx={};journalLocked=heldDirty=false;restore();
}
void recoveryTests(){
 const Preferences priorStore=store;
 const auto priorDisk=diskPages;
 // Both original NVS species and first-write extended species use the same
 // actual acknowledgement and reboot paths. Simulate a cut before and after
 // each NVS write and during/after writing each FAT file.
 int interrupted=0;
 for(int id:{3,originalSpecies+37}){
   for(int cut=1;cut<=8;cut++){
     store=priorStore;diskPages=priorDisk;restartJournal();
     auto& g=view.game;view.destination=7;g.fish=id;g.length=catalog[id].low;g.filed=false;
     g.emptyCast=false;g.timeSlot=2;g.weather=Weather::HeavyRain;g.bait=17;g.enter(Phase::Landed);
     const auto prior=g.progress.book.entries[id];const int grams=g.landedGrams;
     fakeUtc=id==3?1795000000:0;
     holdLanding(false);const uint32_t seq=catchTx.record.sequence;
     writesLeft=cut;testPersistentWrite=cutPower;
     try{finishLanding();}catch(int){++interrupted;}
     testPersistentWrite=nullptr;restartJournal();
     // A cut before the acknowledgement persisted needs a second user tap.
     if(catchTx.stage!=CatchStage::Idle)assert(finishLanding());
     assert(catchTx.stage==CatchStage::Idle && catchTx.record.sequence==seq);
     assert(!finishLanding());restartJournal();
     assert(view.game.progress.book.entries[id].count==prior.count+1);
     CatchRecord r;assert(readCatch(seq,r) && !readCatch(seq+1,r));
     assert(r.species==id && r.cm==catalog[id].low && r.grams==grams && r.utc==fakeUtc);
     assert(bool(r.flags&TimeKnown)==bool(fakeUtc) && r.period==2 && r.weather==2 && r.bait==17 && r.spot==7);
   }
 }
 assert(interrupted==16);
 store=Preferences{};diskPages.clear();HeldFish old{3,catalog[3].low,0};store.putBytes("held-fish",&old,sizeof(old));
 restartJournal();assert(catchTx.stage==CatchStage::Landed && (catchTx.record.flags&LegacyPending));
 assert(!catchTx.record.utc && catchTx.record.spot==255 && catchTx.record.bait==255 && catchTx.record.weather==255);
 assert(finishLanding());restartJournal();assert(catchTx.record.sequence==1 && view.game.progress.book.entries[3].count==1);
 // Cross multiple page boundaries. An identical replay can only keep its row.
 for(unsigned seq=2;seq<=72;seq++){
   CatchRecord r;r.sequence=seq;r.species=3;r.cm=catalog[3].low;
   assert(archiveCatch(r)&&archiveCatch(r));r.grams=42;assert(!archiveCatch(r));
 }
 for(unsigned seq=1;seq<=72;seq++){CatchRecord r;assert(readCatch(seq,r)&&r.sequence==seq);}
 store=priorStore;diskPages=priorDisk;restartJournal();
 printf("PASS %d injected power cuts and retries across NVS, paired FAT history and aggregate pages. Verified valid/unknown UTC, prior-save migration, 72 sequenced rows and preserved metadata.\n",interrupted);
}
int main(){
 assert(readBattery().present && readBattery().charging && readBattery().percent==57);
 auto usb=batteryFromStatus(0x20,0,39);assert(usb.usb&&!usb.present&&!usb.charging&&usb.percent<0);
 auto bad=batteryFromStatus(8,0,127);assert(bad.present&&!bad.usb&&bad.percent<0);
 auto low=batteryFromStatus(8,0,0);assert(low.percent==0&&!low.charging);
 struct Legacy{Entry entries[40];uint8_t rank[3],pad;};Legacy old{};old.entries[4].count=2;old.entries[4].best=20;store.putBytes("atlas-2",&old,sizeof(old));setup();assert(view.game.progress.book.entries[4].count==2);step(42);assert(view.page==Page::Rest&&view.stable);
 tap(120,250);inputG={0,.64f,.7684f};step(55);tap(125,250);assert(view.calibrated&&view.page==Page::Play);
 inputG={0,0,1};step(30);tap(420,16);tap(2,20);assert(view.page==Page::Play);tap(420,16);gridTap(3);assert(view.page==Page::Bench);
 tap(360,307);assert(view.page==Page::TouchCheck);
 tap(463,303);assert(view.touchStep==0);
 for(int i=0;i<9;i++){tap(touchColumn[i%3],touchRow[i/3]);assert(view.touchStep==i+1);}
 tap(90,302);assert(view.page==Page::Bench);
 step(25);inputG={0,.64f,.7684f};step(20);inputG={0,0,1};step(24);
 assert(view.casts==1&&view.lifts==1&&view.degrees<2 && view.game.phase==Phase::Ready);
 encoder=35;step(1);assert(view.raw==35 && view.direction==1 && view.turns>0);
 tap(32,181);assert(view.sound.reverse);encoder=125;step(1);assert(view.direction==-1&&view.turns<0);
 magnet=Field::Weak;step(1);assert(view.raw==-1);magnet=Field::Good;encoder=4000;step(1);assert(view.turns>-.1);
 view.sound.cue=1;tap(181,190);int level=view.sound.cueVolume;tap(301,190);assert(cuePulses==1&&lastMix.cue==0&&lastMix.cueVolume==level);
 step(35);assert(lastMix.cue==1);tap(420,190);tap(345,250);assert(motorPulses==1);
 tap(427,17);gridTap(0);gridTap(2,menuui::gridTop,menuui::waterRow);tap(244,225);tap(240,270);assert(view.page==Page::Arrival && view.game.site==2 && view.sound.site==2);
 uint32_t arrive=view.arrivalStart;inputG={0,.64f,.7684f};step(45);inputG={0,0,1};step(20);
 assert(view.page==Page::Arrival && view.game.phase==Phase::Ready && view.game.age==0);
 while(testClock-arrive<arrival::duration-16)step(1);
 assert(view.page==Page::Arrival);step(2);assert(view.page==Page::Play && view.game.phase==Phase::Ready);
 view.practice=true;tap(420,16);gridTap(0);gridTap(1,menuui::gridTop,menuui::waterRow);tap(240,270);
 assert(view.page==Page::Arrival);tap(230,220);assert(view.page==Page::Play && view.game.phase==Phase::Ready);
 tap(420,16);gridTap(0);tap(240,270);assert(view.page==Page::Play);
 tap(420,16);gridTap(0);gridTap(2,menuui::gridTop,menuui::waterRow);tap(240,270);assert(view.page==Page::Arrival);
 tap(230,220);assert(view.page==Page::Play && view.game.phase==Phase::Ready);
 view.game.phase=Phase::Fight;view.game.fish=20;view.game.line=.01f;view.game.target=6;view.game.length=35;view.practice=true;
 tap(23,287);assert(view.game.phase==Phase::Landed && view.game.progress.book.entries[20].count==0);
 assert(landingPulses==1 && heardLanding.tier==catalog[20].tier && heardLanding.reward==LandingReward::Discovery);
 step(70);tap(240,160);step(70);assert(landingPulses==1 && store.getBytesLength("atlas-3")==sizeof(OriginalBook<52>));
 tap(425,17);gridTap(2);assert(view.page==Page::Journey);gridTap(3,menuui::workshopTop,menuui::workshopRow);assert(view.game.progress.rank[1]==1);
 view.game.progress=Progress{};restore();assert(view.timeMode==2&&view.game.progress.rank[1]==1&&view.game.progress.book.entries[20].count==1&&view.calibrated);
 // Navigate every scene-backed sheet at its physical LCD coordinates.
 view.page=Page::Play;view.practice=true;view.game.line=view.game.target;view.game.enter(Phase::Fight);
 tap(420,16);assert(view.page==Page::Hub);
 uint32_t pausedAge=view.game.age;step(20);assert(view.game.age==pausedAge);
 gridTap(1);assert(view.page==Page::Book&&view.bookWater==siteCount&&view.bookFilter==BookFilter::All&&view.game.progress.book.waterCount(view.bookWater,view.destination,view.bookFilter)==fishCount);
 gridTap(0,menuui::gridTop,86);assert(view.page==Page::BookDetail&&view.bookSpecies>=0);
 tap(406,43);assert(view.page==Page::Book);
 tap(menuui::x+246,menuui::y+246);assert(view.page==Page::CatchHistory&&view.history.sequence==1&&view.history.species==20&&!view.historyError);
 tap(406,43);assert(view.page==Page::Book);
 int oldPage=view.bookPage;tap(405,267);const int visible=view.game.progress.book.waterCount(view.bookWater,view.destination,view.bookFilter);
 assert(view.bookPage==(oldPage+1)%std::max(1,(visible+menuui::bookRows-1)/menuui::bookRows));
 tap(406,43);assert(view.page==Page::Hub);
 gridTap(4);assert(view.page==Page::Options);int volume=view.sound.volume;
 gridTap(1);assert(view.sound.volume==(volume+1)%4);
 tap(406,43);gridTap(6);assert(view.page==Page::Network);
 gridTap(4,menuui::networkTop,menuui::networkRow);assert(view.page==Page::Controller&&controllerOpen);
 gridTap(0,menuui::controllerTop,menuui::controllerRow);assert(controllerArmed);
 gridTap(1,menuui::controllerTop,menuui::controllerRow);assert(view.page==Page::Network&&!controllerOpen&&!controllerArmed);
 tap(406,43);assert(view.page==Page::Hub);tap(406,43);assert(view.page==Page::Play);
 if(fishCount>originalSpecies){
   const int id=fishCount-1;
   view.page=Page::Play;view.game.fish=id;view.game.length=catalog[id].low;view.game.filed=false;
   view.game.enter(Phase::Landed);holdLanding(false);diskWriteOK=false;tap(240,160);
   assert(view.saveFailed && !view.game.filed && !view.game.progress.book.entries[id].count);
   diskWriteOK=true;tap(240,160);assert(view.game.filed && !view.saveFailed);
   step(70);view.game.progress.book.entries[id]={};restore();
   assert(view.game.progress.book.entries[id].count==1);
   Entry next=view.game.progress.book.entries[id];next.count=2;assert(saveExtraEntry(id,next));
   char key[16];sectorName(key,sizeof(key),(id-originalSpecies)/journalPageEntries,1);
   diskPages[key].resize(7);view.game.progress.book.entries[id]={};restore();
   assert(view.game.progress.book.entries[id].count==1);
   assert(store.getBytesLength("atlas-3")==420);
   const auto savedPages=diskPages;diskPages.clear();
   for(int i=originalSpecies;i<fishCount;++i){
     Entry entry;entry.count=1;entry.best=catalog[i].low;assert(saveExtraEntry(i,entry));
     entry.count=2;entry.best=catalog[i].high;assert(saveExtraEntry(i,entry));
   }
   const size_t pages=(fishCount-originalSpecies+journalPageEntries-1)/journalPageEntries;
   assert(diskPages.size()==2*pages);
   Journal complete;assert(restoreExtraBook(complete));
   for(int i=originalSpecies;i<fishCount;++i){
     assert(complete.entries[i].count==2 && complete.entries[i].best==catalog[i].high);
   }
   diskPages=savedPages;
   printf("PASS %d extended records across %zu two-slot FAT pages, newest-page recovery, failed-save retry and legacy 420-byte NVS.\n",fishCount-originalSpecies,pages);

 }
 puts("PASS compact overlay touch mapping, fishing-state pause, edge dismissal and resume.");
 // Use the physical menu coordinates and actual Preferences read/write paths.
 view.page=Page::Play;view.game.enter(Phase::Ready);
 tap(420,16);gridTap(2);assert(view.page==Page::Journey);
 tap(menuui::x+195,menuui::y+12);assert(view.page==Page::Bait);
 gridTap(1,menuui::gridTop,menuui::baitRow);tap(menuui::x+330,menuui::y+menuui::depthY+23);
 assert(view.game.bait==13 && store.getUChar("bait",0)==13);
 view.game.bait=0;restore();assert(view.game.bait==13);
 view.game.enter(Phase::Fight);tap(menuui::x+30,menuui::y+50);
 assert(view.game.bait==13 && store.getUChar("bait",0)==13);
 // The live sketch audio and motor outputs must also remain quiet on an empty cast.
 view.game.enter(Phase::Ready);view.game.setBait(4);view.page=Page::Play;view.practice=true;
 view.destination=0;view.game.site=destinations[0].pool;view.game.arriveAt(0);view.timeMode=0;view.game.timeSlot=0;
 view.game.beginSession(19);view.game.arriveAt(0);view.rumble=2;view.sound.cue=0;view.sound.cueVolume=3;
 tap(240,280);assert(view.game.phase==Phase::Flight && view.game.emptyCast);
 const int audioBefore=cuePulses,vibrationBefore=motorPulses,pointsBefore=view.game.progress.points();
 step(500);assert(view.game.phase==Phase::Lost && view.game.reason==Reason::NoBite);
 assert(cuePulses==audioBefore && motorPulses==vibrationBefore && view.game.progress.points()==pointsBefore);
 puts("PASS native bait/depth touches, Preferences restore, live-cast lockout and empty-cast audio, rumble and score.");
 recoveryTests();

 puts("PASS sketch-loop bench calibration, live cast/lift counts, signed wrapped encoder and reversal, magnet recovery, independent cue audition, rumble audition, travel, upgrade and saved-state restore including v0.2 journal migration and time selection.");
}
