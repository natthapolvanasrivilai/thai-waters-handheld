#include "RodController.h"
#include "RodHidProtocol.h"
#include <BLEDevice.h>
#include <BLEHIDDevice.h>
#include <BLESecurity.h>
#include <atomic>
#include <host/ble_gap.h>
#include <host/ble_gatt.h>
#include <host/ble_hs_mbuf.h>

namespace {
constexpr uint16_t none=BLE_HS_CONN_HANDLE_NONE;
BLEServer* server=nullptr;
BLEHIDDevice* hid=nullptr;
BLECharacteristic *report=nullptr,*boot=nullptr;
std::atomic<uint16_t> connection{none};
std::atomic<bool> subscribed{false},bootSubscribed{false},lost{false},suspended{false};
bool enabled=false,armed=false,closing=false,failed=false,disconnectRequested=false;
unsigned passkey=0;
uint32_t closeAt=0,nextAdvertise=0;
int gauge=-1;
rodhid::Stream stream;
uint8_t descriptor[]={
  0x05,0x01,0x09,0x06,0xa1,0x01,0x85,0x01, // Keyboard, report ID 1
  0x05,0x07,0x19,0xe0,0x29,0xe7,0x15,0x00,0x25,0x01,0x75,0x01,0x95,0x08,0x81,0x02,
  0x75,0x08,0x95,0x01,0x81,0x01, // Modifier and reserved bytes
  0x05,0x08,0x19,0x01,0x29,0x05,0x95,0x05,0x75,0x01,0x91,0x02,0x95,0x01,0x75,0x03,0x91,0x01,
  0x05,0x07,0x19,0x00,0x29,0x65,0x15,0x00,0x25,0x65,0x75,0x08,0x95,0x06,0x81,0x00,0xc0
};
class Peer : public BLEServerCallbacks {
  void onConnect(BLEServer*,ble_gap_conn_desc* d) override {connection.store(d->conn_handle);}
  void onDisconnect(BLEServer*,ble_gap_conn_desc*) override {
    connection.store(none);subscribed=false;bootSubscribed=false;suspended=false;lost=true;
  }
} peer;
class Reports : public BLECharacteristicCallbacks {
  void onSubscribe(BLECharacteristic* c,ble_gap_conn_desc*,uint16_t flags) override {
    if(c==boot)bootSubscribed=(flags&1)!=0;else subscribed=(flags&1)!=0;
  }
  void onWrite(BLECharacteristic* c,ble_gap_conn_desc*) override {
    const auto value=c->getValue();if(value.length()==1)suspended=(value[0]==0);
  }
} reports;
BLECharacteristic* activeReport(){
  if(!hid)return nullptr;
  const auto p=hid->protocolMode()->getValue();
  if(p.length() && p[0]==0)return bootSubscribed?boot:nullptr;
  return subscribed?report:nullptr;
}
bool sendKey(int usage){
  BLECharacteristic* ch=activeReport();const auto conn=connection.load();
  if(!ch || conn==none)return false;
  uint8_t value[8]={};value[2]=uint8_t(usage);
  auto* packet=ble_hs_mbuf_from_flat(value,sizeof(value));
  if(!packet)return false;
  if(ble_gatts_notify_custom(conn,ch->getHandle(),packet)!=0)return false;
  ch->setValue(value,sizeof(value));return true;
}
void resetReports(){
  const uint8_t neutral[8]={},reportMode=1;
  report->setValue(neutral,sizeof(neutral));boot->setValue(neutral,sizeof(neutral));
  hid->protocolMode()->setValue(&reportMode,1);
}
}
bool beginRodController(int batteryPercent){
  if(closing)return false;
  if(enabled)return !failed;
  if(server){
    passkey=BLESecurity::setPassKey(false);
    failed=!BLEDevice::getAdvertising()->start();enabled=true;return !failed;
  }
  failed=!BLEDevice::init("Thai Waters Rod");
  if(failed)return false;
  BLESecurity::setAuthenticationMode(true,true,true);
  BLESecurity::setCapability(BLE_HS_IO_DISPLAY_ONLY);
  BLESecurity::setInitEncryptionKey();BLESecurity::setRespEncryptionKey();
  BLESecurity::setForceAuthentication(true);
  passkey=BLESecurity::setPassKey(false);
  server=BLEDevice::createServer();server->setCallbacks(&peer);
  server->advertiseOnDisconnect(false);
  hid=new BLEHIDDevice(server);
  hid->manufacturer("Thai Waters");hid->pnp(1,0xffff,1,0x0091);hid->hidInfo(0,2);
  report=hid->inputReport(1);hid->outputReport(1);
  boot=hid->bootInput();boot->setReadProperty(true);hid->bootOutput();
  report->setCallbacks(&reports);boot->setCallbacks(&reports);hid->hidControl()->setCallbacks(&reports);
  hid->reportMap(descriptor,sizeof(descriptor));
  resetReports();
  hid->startServices();gauge=-1;
  if(batteryPercent>=0 && batteryPercent<=100){gauge=batteryPercent;hid->setBatteryLevel(gauge);}
  auto* adv=BLEDevice::getAdvertising();adv->setAppearance(HID_KEYBOARD);
  adv->addServiceUUID(hid->hidService()->getUUID());adv->setName("Thai Waters Rod");adv->setScanResponse(true);
  failed=!adv->start();enabled=true;armed=false;stream={};return !failed;
}
bool rodControllerReady(){
  ble_gap_conn_desc d{};
  return enabled && !closing && !suspended && activeReport() && ble_gap_conn_find(connection.load(),&d)==0 &&
         d.sec_state.encrypted && d.sec_state.authenticated && d.sec_state.bonded;
}
bool rodControllerStreaming(){return armed && !closing;}
void armRodController(){
  if(!rodControllerReady())return;
  if(armed)sendKey(0);
  armed=!armed;stream={};
}
void endRodController(){
  if(!enabled || closing)return;
  sendKey(0);armed=false;closing=true;disconnectRequested=false;closeAt=millis();
  BLEDevice::getAdvertising()->stop();
}
unsigned rodPairCode(){return passkey;}
const char* rodControllerStatus(){
  if(failed)return "Bluetooth unavailable. Exit and retry.";
  if(closing)return "Turning Bluetooth off";
  if(armed)return "Sending controls to phone";
  if(rodControllerReady())return "Paired. Open the game and tap Start.";
  return connection.load()==none?"Pair Thai Waters Rod in phone Settings":"Waiting for secure keyboard connection";
}
void tickRodController(uint32_t now,bool cast,bool lift,float turns,float pitch,int batteryPercent){
  if(!enabled)return;
  if(closing){
    auto conn=connection.load();
    if(conn!=none){
      if(now-closeAt>=(disconnectRequested?500u:45u)){server->disconnect(conn);disconnectRequested=true;closeAt=now;}
      return;
    }
    if(now-closeAt<100)return;
    // Arduino-ESP32 3.3.10 does not deep-free its server's GATT tree.
    // Keep one service allocation per boot. The disconnected, non-advertising
    // controller has no scheduled radio packets until the next explicit start.
    BLEDevice::getAdvertising()->stop();
    resetReports();enabled=false;lost=false;closing=false;suspended=false;nextAdvertise=0;return;
  }
  if(lost.exchange(false)){
    resetReports();armed=false;stream={};passkey=BLESecurity::setPassKey(false);
    nextAdvertise=now+100;
  }
  if(nextAdvertise && int32_t(now-nextAdvertise)>=0){
    nextAdvertise=0;if(connection.load()==none)BLEDevice::getAdvertising()->start();
  }
  if(batteryPercent>=0 && batteryPercent<=100 && batteryPercent!=gauge){
    gauge=batteryPercent;hid->setBatteryLevel(gauge);
  }
  if(!armed)return;
  if(!rodControllerReady()){sendKey(0);armed=false;stream={};return;}
  if(!stream.initial)stream.sample(turns,cast,lift,pitch);
  const int key=stream.next(now);
  if(key!=rodhid::Stream::idle && sendKey(key))stream.sent(key,now);
}

