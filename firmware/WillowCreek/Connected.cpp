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
bool radio=false,pairing=false,trying=false,clockValid=false;
bool dropping=false,streaming=false;
uint32_t pairStart=0,attemptStart=0,lastSample=0,lastClock=0;
std::atomic<bool> synced{false};
const char* clockSource="RTC";
const char* hint="Offline";
int period=0;
void connectSaved(){
 if(!radio)return;
 WiFi.mode(WIFI_STA);WiFi.setSleep(true);
 if(saved.ssid[0]){WiFi.begin(saved.ssid,saved.pass);hint="Joining saved network";}else hint="Open Phone setup to join Wi-Fi";
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
 tm u{};u.tm_sec=decimal(b[0]);u.tm_min=decimal(b[1]);u.tm_hour=decimal(b[2]);u.tm_mday=decimal(b[3]);u.tm_mon=decimal(b[5])-1;u.tm_year=100+decimal(b[6]);
 if(u.tm_sec>59||u.tm_min>59||u.tm_hour>23||u.tm_mday<1||u.tm_mday>31||u.tm_mon<0||u.tm_mon>11||u.tm_year<125)return;
 timeval tv{mktime(&u),0};settimeofday(&tv,nullptr);clockValid=true;
}
void refreshClock(){
 if(!clockValid)return;
 time_t bangkok=time(nullptr)+7*3600;tm local{};gmtime_r(&bangkok,&local);
 int h=local.tm_hour;period=h>=5&&h<8?0:h>=8&&h<17?1:h>=17&&h<20?2:3;
 snprintf(clockText,sizeof(clockText),"%02d:%02d ICT",h,local.tm_min);
}
bool localPhone(){return pairing&&portal.client().localIP()==WiFi.softAPIP()&&portal.hostHeader()==WiFi.softAPIP().toString();}
void form(){
 if(!localPhone()){portal.send(403);return;}
 portal.sendHeader("Cache-Control","no-store");
 String html=F("<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><title>Thai Waters Wi-Fi</title><style>body{font:18px system-ui;max-width:26em;margin:3em auto;padding:1em;background:#edf1e5;color:#193f36}label,input,button{display:block;margin:12px 0;padding:6px}</style><h1>Join Wi-Fi</h1><form method=post action=/join><label>2.4 GHz network name<input name=s maxlength=32 required></label><label>Network password<input name=p type=password maxlength=63></label><input type=hidden name=t value='");
 html+=nonce;html+=F("'><button>Connect device</button></form>");portal.send(200,"text/html",html);
}
void join(){
 if(!localPhone()||portal.arg("t")!=nonce){portal.send(403);return;}
 String s=portal.arg("s"),p=portal.arg("p");
 if(s.isEmpty()||s.length()>32||p.length()>63||(p.length()&&p.length()<8)){portal.send(400,"text/plain","Check network name and password length.");return;}
 candidate={};s.toCharArray(candidate.ssid,sizeof(candidate.ssid));p.toCharArray(candidate.pass,sizeof(candidate.pass));
 portal.send(200,"text/plain","Joining. Check the handheld for the result.");WiFi.disconnect(false,false);WiFi.begin(candidate.ssid,candidate.pass);trying=true;attemptStart=millis();hint="Testing network credentials";
}
void sampleUSB(){
 auto s=hardware::sample();
 Serial.printf("{\"api\":1,\"ms\":%lu,\"accel_ok\":%d,\"gyro_ok\":%d,\"accel_g\":[%.5f,%.5f,%.5f],\"gyro_dps\":[%.4f,%.4f,%.4f],\"accel_raw\":[%d,%d,%d],\"gyro_raw\":[%d,%d,%d],\"field\":%d,\"reel_counts\":%d}\n",(unsigned long)s.uptimeMs,s.accelOK,s.gyroOK,s.accelG.x,s.accelG.y,s.accelG.z,s.gyroDps.x,s.gyroDps.y,s.gyroDps.z,s.accelRaw[0],s.accelRaw[1],s.accelRaw[2],s.gyroRaw[0],s.gyroRaw[1],s.gyroRaw[2],int(s.field),s.reel);
}
void usb(String line){
 if(line=="api1 sample"){sampleUSB();return;}
 if(line=="api1 caps"){Serial.println("{\"api\":1,\"minor\":0,\"board\":\"riffle-e-31137\",\"fw\":4,\"inputs\":[\"accel_raw\",\"gyro_raw\",\"reel_counts\"],\"stream_hz\":10}");return;}
 bool ok=false;
 if(line=="api1 gyro on"||line=="api1 gyro off")ok=hardware::gyroPower(line.endsWith(" on"));
 else if(line=="api1 stream on"||line=="api1 stream off"){streaming=line.endsWith(" on");ok=true;}
 else if(line.startsWith("api1 trust ")&&!updateBusy()){String k=line.substring(11);ok=releaseKeyValid(k)&&settings.putString("release-key",k)>0;}
 else if(line.startsWith("api1 feed https://")&&!updateBusy()){String url=line.substring(10);ok=url.length()<=240&&url.indexOf(' ')==-1&&settings.putString("release-feed",url)>0;}
 else if(line=="api1 forget"&&!updateBusy()){stopPairing();saved={};settings.remove("network");WiFi.disconnect(true,false);radio=false;settings.putBool("radio",false);ok=true;}
 Serial.println(ok?"{\"ok\":true}":"{\"ok\":false}");
}
}
void beginConnected(){
 settings.begin("tw-connect",false);setenv("TZ","UTC0",1);tzset();loadClock();refreshClock();
 settings.getBytes("network",&saved,sizeof(saved));saved.ssid[32]=0;saved.pass[64]=0;
 WiFi.persistent(false);radio=settings.getBool("radio",false);
 esp_sntp_set_time_sync_notification_cb([](timeval*){synced.store(true);});
 portal.on("/",HTTP_GET,form);portal.on("/join",HTTP_POST,join);
 if(radio)connectSaved();
}
void startPairing(){
 if(pairing||updateBusy())return;
 radio=true;WiFi.mode(WIFI_AP_STA);
 snprintf(apName,sizeof(apName),"ThaiWaters-%04X",unsigned(ESP.getEfuseMac()&65535));
 snprintf(apPass,sizeof(apPass),"%08lX%04lX",(unsigned long)esp_random(),(unsigned long)(esp_random()&65535));
 nonce=String(esp_random(),HEX)+String(esp_random(),HEX);
 if(!WiFi.softAP(apName,apPass)){hint="Could not start phone setup";WiFi.mode(WIFI_STA);return;}
 pairing=true;pairStart=millis();portal.begin();hint="Join this network on your phone";
 snprintf(instructions,sizeof(instructions),"Password %s   Open http://192.168.4.1",apPass);
}
void stopPairing(){
 if(!pairing)return;
 portal.stop();WiFi.softAPdisconnect(false);pairing=trying=false;candidate={};nonce="";apPass[0]=instructions[0]=0;
 if(!settings.getBool("radio",false)){WiFi.mode(WIFI_OFF);radio=false;}
 else connectSaved();
}
bool radioEnabled(){return radio;}
void toggleRadio(){
 if(updateBusy())return;
 bool next=!radio;stopPairing();radio=next;settings.putBool("radio",radio);
 if(radio)connectSaved();else {WiFi.disconnect(true,false);WiFi.mode(WIFI_OFF);hint="Offline";}
}
const char* networkStatus(){if(!pairing&&radio&&WiFi.status()==WL_CONNECTED&&!clockValid)return "Connected - waiting for time sync";return pairing?hint:!radio?"Radio off":WiFi.status()==WL_CONNECTED?"Connected to Wi-Fi":hint;}
const char* setupName(){return pairing?apName:clockValid?clockSource:"Clock awaiting network sync";}
const char* setupCode(){return pairing?instructions:"Pond time zone: Asia/Bangkok (UTC+7)";}
const char* pondClock(){return clockText;}
int pondPeriod(){return period;}
void checkUpdate(){
 if(!radio||WiFi.status()!=WL_CONNECTED){hint="Connect to Wi-Fi first";return;}
 if(!clockValid){hint="Waiting for network time";return;}
 fetchRelease(settings.getString("release-feed",""),settings.getString("release-key",""));
}
void tickConnected(){
 static bool ntp=false;
 if(pairing){
  portal.handleClient();
  if(trying&&WiFi.status()==WL_CONNECTED&&WiFi.SSID()==candidate.ssid){if(settings.putBytes("network",&candidate,sizeof(candidate))==sizeof(candidate)){saved=candidate;settings.putBool("radio",true);stopPairing();}else {trying=false;hint="Could not save Wi-Fi";}}
  else if(trying&&millis()-attemptStart>18000){trying=false;hint="Join failed. Retry on your phone";}
  if(pairing&&millis()-pairStart>300000)stopPairing();
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

