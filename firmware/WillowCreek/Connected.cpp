#include "Connected.h"
#include "UpdateFeed.h"
#include "HardwareAPI.h"
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <esp_sntp.h>
#include <sys/time.h>
#include <atomic>

namespace {
Preferences settings;
WebServer portal(80);
struct Network {char ssid[33],pass[65];} saved{},candidate{};
char apName[25]{},apPass[20]{},instructions[85]{},clockText[32]="Clock needs sync";
String nonce,command;
enum class Join { Idle, LeavePrevious, Connecting };
enum class SaveNote { None, Session, Failed, KeptPrevious, RadioPreferenceFailed };
Join joinStage=Join::Idle;
SaveNote saveNote=SaveNote::None;
bool radio=false,pairing=false,clockValid=false;
bool priorRadio=false,portalChangedStation=false,remember=false,joiningSaved=false;
bool dropping=false,streaming=false;
uint32_t pairStart=0,attemptStart=0,savedStart=0,lastSample=0,lastClock=0;
std::atomic<bool> synced{false};
const char* clockSource="RTC";
const char* hint="Offline";
int period=0;
void clearBytes(void* value,size_t length){
 auto* p=static_cast<volatile char*>(value);
 while(length--)*p++=0;
}
void clearAttempt(){
 joinStage=Join::Idle;remember=false;clearBytes(&candidate,sizeof(candidate));
}
void closePortal(){
 portal.stop();WiFi.softAPdisconnect(false);pairing=false;clearAttempt();nonce="";
 clearBytes(apPass,sizeof(apPass));clearBytes(instructions,sizeof(instructions));
}
void connectSaved(){
 if(!radio)return;
 saveNote=SaveNote::None;joiningSaved=false;
 if(!WiFi.mode(WIFI_STA)){hint="Could not start Wi-Fi";return;}
 WiFi.setSleep(true);
 if(saved.ssid[0]){
  WiFi.begin(saved.ssid,saved.pass);savedStart=millis();joiningSaved=true;hint="Joining saved network";
 }else hint="Open Phone setup to join Wi-Fi";
}
void rememberConnected(){
 if(!remember){saveNote=SaveNote::Session;return;}
 // One existing network slot. Don't silently replace another saved setup.
 if(saved.ssid[0]){
  if(strcmp(saved.ssid,candidate.ssid)||strcmp(saved.pass,candidate.pass)){
   saveNote=SaveNote::KeptPrevious;return;
  }
 }else{
  if(settings.putBytes("network",&candidate,sizeof(candidate))!=sizeof(candidate)){
   saveNote=SaveNote::Failed;return;
  }
  saved=candidate;
 }
 if(!settings.getBool("radio",false)&&!settings.putBool("radio",true))
  saveNote=SaveNote::RadioPreferenceFailed;
}
bool rtcIO(uint8_t* b,bool write){
 Wire.beginTransmission(0x51);Wire.write(4);
 if(write){Wire.write(b,7);return Wire.endTransmission()==0;}
 if(Wire.endTransmission(false)!=0||Wire.requestFrom(uint8_t(0x51),size_t(7))!=7)return false;
 return Wire.readBytes(b,7)==7;
}
int bcd(int x){return (x/10)*16+x%10;}
int decimal(int x){return (x/16)*10+x%16;}
void storeClock(time_t t){
 tm u{};gmtime_r(&t,&u);
 uint8_t b[]={uint8_t(bcd(u.tm_sec)),uint8_t(bcd(u.tm_min)),uint8_t(bcd(u.tm_hour)),uint8_t(bcd(u.tm_mday)),uint8_t(u.tm_wday),uint8_t(bcd(u.tm_mon+1)),uint8_t(bcd(u.tm_year-100))};
 if(rtcIO(b,true)&&!settings.getBool("utc-set",false))settings.putBool("utc-set",true);
}
void loadClock(){
 uint8_t b[7]{};if(!settings.getBool("utc-set",false)||!rtcIO(b,false)||(b[0]&128))return;
 for(auto value:b)if((value&15)>9 || (value>>4)>9)return;
 tm u{};u.tm_sec=decimal(b[0]);u.tm_min=decimal(b[1]);u.tm_hour=decimal(b[2]);u.tm_mday=decimal(b[3]);u.tm_mon=decimal(b[5])-1;u.tm_year=100+decimal(b[6]);
 if(u.tm_sec>59||u.tm_min>59||u.tm_hour>23||u.tm_mday<1||u.tm_mday>31||u.tm_mon<0||u.tm_mon>11||u.tm_year<125)return;
 int month=u.tm_mon,day=u.tm_mday;
 timeval tv{mktime(&u),0};
 if(u.tm_mon!=month || u.tm_mday!=day || tv.tv_sec<1735689600)return;
 clockValid=settimeofday(&tv,nullptr)==0;
}
void refreshClock(){
 if(!clockValid)return;
 time_t bangkok=time(nullptr)+7*3600;tm local{};gmtime_r(&bangkok,&local);
 int h=local.tm_hour;period=h>=5&&h<8?0:h>=8&&h<17?1:h>=17&&h<20?2:3;
 snprintf(clockText,sizeof(clockText),"%02d:%02d ICT",h,local.tm_min);
}
bool localPhone(){return pairing&&portal.client().localIP()==WiFi.softAPIP()&&portal.hostHeader()==WiFi.softAPIP().toString();}
void form(){
 portal.sendHeader("Cache-Control","no-store");
 if(!localPhone()){portal.send(403);return;}
 String html=F("<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><title>Thai Waters Wi-Fi</title><style>body{font:18px system-ui;max-width:26em;margin:3em auto;padding:1em;background:#edf1e5;color:#193f36}label,input,button{display:block;margin:12px 0;padding:6px}</style><h1>Join Wi-Fi</h1><form method=post action=/join><label>2.4 GHz network name<input name=s maxlength=32 required></label><label>Network password<input name=p type=password maxlength=63 autocomplete=off></label><input type=hidden name=t value='");
 html+=nonce;html+=F("'><label><input type=checkbox name=r value=1> Remember on this device</label><p>Unchecked: this connection is used only until Wi-Fi is turned off or the device restarts. A saved network is not replaced.</p><button>Connect device</button></form>");portal.send(200,"text/html",html);
}
void join(){
 portal.sendHeader("Cache-Control","no-store");
 if(!localPhone()||portal.arg("t")!=nonce){portal.send(403);return;}
 if(joinStage!=Join::Idle){portal.send(409,"text/plain","A connection attempt is already in progress.");return;}
 String s=portal.arg("s"),p=portal.arg("p");
 if(s.isEmpty()||s.length()>32||p.length()>63||(p.length()&&p.length()<8)){portal.send(400,"text/plain","Check network name and password length.");return;}
 clearAttempt();s.toCharArray(candidate.ssid,sizeof(candidate.ssid));p.toCharArray(candidate.pass,sizeof(candidate.pass));
 remember=portal.arg("r")=="1";portalChangedStation=true;joiningSaved=false;saveNote=SaveNote::None;
 // Start only after the previous association is down, including same-SSID retries.
 WiFi.disconnect(false,false);joinStage=Join::LeavePrevious;attemptStart=millis();
 hint="Joining Wi-Fi";portal.send(200,"text/plain","Joining. Check the handheld for the result.");
}
void sampleUSB(){
 auto s=hardware::sample();
 Serial.printf("{\"api\":1,\"ms\":%lu,\"accel_ok\":%d,\"gyro_ok\":%d,\"accel_g\":[%.5f,%.5f,%.5f],\"gyro_dps\":[%.4f,%.4f,%.4f],\"accel_raw\":[%d,%d,%d],\"gyro_raw\":[%d,%d,%d],\"field\":%d,\"reel_counts\":%d}\n",(unsigned long)s.uptimeMs,s.accelOK,s.gyroOK,s.accelG.x,s.accelG.y,s.accelG.z,s.gyroDps.x,s.gyroDps.y,s.gyroDps.z,s.accelRaw[0],s.accelRaw[1],s.accelRaw[2],s.gyroRaw[0],s.gyroRaw[1],s.gyroRaw[2],int(s.field),s.reel);
}
void usb(String line){
 if(line=="api1 catches"){printCatchRecord(0);return;}
 if(line.startsWith("api1 catch ")){
   const String index=line.substring(11);char* end=nullptr;
   const unsigned long value=strtoul(index.c_str(),&end,10);
   if(index.length() && isDigit(index[0]) && end && !*end && value)printCatchRecord(value);
   else Serial.println("{\"ok\":false}");
   return;
 }
 if(line=="api1 sample"){sampleUSB();return;}
 if(line=="api1 caps"){Serial.println("{\"api\":1,\"minor\":0,\"board\":\"riffle-e-31137\",\"fw\":6,\"inputs\":[\"accel_raw\",\"gyro_raw\",\"reel_counts\"],\"stream_hz\":10}");return;}
 bool ok=false;
 if(line=="api1 gyro on"||line=="api1 gyro off")ok=hardware::gyroPower(line.endsWith(" on"));
 else if(line=="api1 stream on"||line=="api1 stream off"){streaming=line.endsWith(" on");ok=true;}
 else if(line.startsWith("api1 trust ")&&!updateBusy()){String k=line.substring(11);ok=releaseKeyValid(k)&&settings.putString("release-key",k)>0;}
 else if(line.startsWith("api1 feed https://")&&!updateBusy()){String url=line.substring(10);ok=url.length()<=240&&url.indexOf(' ')==-1&&settings.putString("release-feed",url)>0;}
 else if(line=="api1 forget"&&!updateBusy()){stopPairing();saved={};settings.remove("network");WiFi.disconnect(true,false);radio=false;joiningSaved=false;saveNote=SaveNote::None;settings.putBool("radio",false);ok=true;}
 Serial.println(ok?"{\"ok\":true}":"{\"ok\":false}");
}
}
void beginConnected(){
 settings.begin("tw-connect",false);setenv("TZ","UTC0",1);tzset();loadClock();refreshClock();
 if(settings.getBytes("network",&saved,sizeof(saved))!=sizeof(saved))clearBytes(&saved,sizeof(saved));
 saved.ssid[32]=0;saved.pass[64]=0;
 // The Arduino 3.3.10 low-level init selects WIFI_STORAGE_RAM before any mode or begin.
 WiFi.persistent(false);radio=settings.getBool("radio",false);
 esp_sntp_set_time_sync_notification_cb([](timeval*){synced.store(true);});
 portal.on("/",HTTP_GET,form);portal.on("/join",HTTP_POST,join);
 if(radio)connectSaved();
}
void startPairing(){
 if(pairing||updateBusy())return;
 priorRadio=radio;portalChangedStation=false;clearAttempt();
 if(!WiFi.mode(WIFI_AP_STA)){hint="Could not start phone setup";return;}
 radio=true;
 snprintf(apName,sizeof(apName),"ThaiWaters-%04X",unsigned(ESP.getEfuseMac()&65535));
 snprintf(apPass,sizeof(apPass),"%08lX%04lX",(unsigned long)esp_random(),(unsigned long)(esp_random()&65535));
 nonce=String(esp_random(),HEX)+String(esp_random(),HEX);
 if(!WiFi.softAP(apName,apPass)){
  nonce="";clearBytes(apPass,sizeof(apPass));radio=priorRadio;
  WiFi.mode(radio?WIFI_STA:WIFI_OFF);hint="Could not start phone setup";return;
 }
 pairing=true;pairStart=millis();portal.begin();hint="Join this network on your phone";
 snprintf(instructions,sizeof(instructions),"Password %s   Open http://192.168.4.1",apPass);
}
void stopPairing(){
 if(!pairing)return;
 if(portalChangedStation)WiFi.disconnect(false,false);
 closePortal();radio=priorRadio;
 if(!radio){WiFi.mode(WIFI_OFF);hint="Wi-Fi disconnected";}
 else if(portalChangedStation)connectSaved();
 else{WiFi.mode(WIFI_STA);hint="Wi-Fi disconnected";}
}
bool radioEnabled(){return radio;}
void toggleRadio(){
 if(updateBusy())return;
 bool next=!radio;stopPairing();radio=next;settings.putBool("radio",radio);
 if(radio)connectSaved();else {WiFi.disconnect(true,false);WiFi.mode(WIFI_OFF);joiningSaved=false;hint="Wi-Fi disconnected";}
}
const char* networkStatus(){
 if(pairing)return hint;
 if(!radio)return "Radio off";
 if(WiFi.status()!=WL_CONNECTED)return hint;
 if(saveNote==SaveNote::Session)return "Wi-Fi connected for this session";
 if(saveNote==SaveNote::Failed)return "Wi-Fi connected; not saved";
 if(saveNote==SaveNote::KeptPrevious)return "Wi-Fi connected; prior network kept";
 if(saveNote==SaveNote::RadioPreferenceFailed)return "Wi-Fi connected; auto-join not saved";
 return "Wi-Fi connected";
}
const char* setupName(){return pairing?apName:clockValid?clockSource:"Clock awaiting network sync";}
const char* setupCode(){return pairing?instructions:"Pond time zone: Asia/Bangkok (UTC+7)";}
const char* pondClock(){return clockText;}
uint32_t pondUtc(){
 const time_t now=time(nullptr);
 return clockValid && now>=1735689600 && uint64_t(now)<=UINT32_MAX?uint32_t(now):0;
}
int pondPeriod(){return period;}
void checkUpdate(){
 if(!radio||WiFi.status()!=WL_CONNECTED){hint="Connect to Wi-Fi first";return;}
 if(!clockValid){hint="Waiting for network time";return;}
 fetchRelease(settings.getString("release-feed",""),settings.getString("release-key",""));
}
void tickConnected(){
 static bool ntp=false;
 if(pairing){
  if(millis()-pairStart>=300000)stopPairing();
  else{
   portal.handleClient();
   if(joinStage!=Join::Idle&&millis()-attemptStart>=18000){
    WiFi.disconnect(false,false);clearAttempt();hint="Wi-Fi join failed. Retry on phone";
   }else if(joinStage==Join::LeavePrevious&&WiFi.status()!=WL_CONNECTED){
    WiFi.begin(candidate.ssid,candidate.pass);joinStage=Join::Connecting;
   }else if(joinStage==Join::Connecting&&WiFi.status()==WL_CONNECTED&&WiFi.SSID()==candidate.ssid){
    rememberConnected();
    closePortal();WiFi.mode(WIFI_STA);WiFi.setSleep(true);
    // Keep the confirmed session. Do not restart STA using saved credentials.
    hint="Wi-Fi disconnected";
   }
  }
 }else if(joiningSaved){
  if(WiFi.status()==WL_CONNECTED){joiningSaved=false;hint="Wi-Fi disconnected";}
  else if(millis()-savedStart>=18000){joiningSaved=false;hint="Could not join saved Wi-Fi";}
 }
 if(radio&&WiFi.status()==WL_CONNECTED&&!ntp){configTime(0,0,"time.cloudflare.com","pool.ntp.org");ntp=true;}
 if(synced.exchange(false)){clockValid=true;clockSource="Network time";storeClock(time(nullptr));refreshClock();}
 if(millis()-lastClock>=1000){lastClock=millis();refreshClock();}
 for(int budget=64;budget--&&Serial.available();){
  char c=Serial.read();if(c=='\r')continue;
  if(c=='\n'){if(!dropping&&command.length())usb(command);command="";dropping=false;}
  else if(command.length()<260&&!dropping)command+=c;else dropping=true;
 }
 if(streaming&&millis()-lastSample>=100){lastSample=millis();if(Serial)sampleUSB();}
}

