#pragma once
#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <functional>
#include <map>
#include <string>
#include <utility>
struct String:std::string{
 using std::string::string;
 using std::string::operator=;
 String(std::string v):std::string(std::move(v)){}
 String(unsigned v,int){char text[16];snprintf(text,sizeof(text),"%x",v);assign(text);}
 bool isEmpty()const{return empty();}
 void toCharArray(char* p,size_t n)const{snprintf(p,n,"%s",c_str());}
 bool startsWith(const char* a)const{return rfind(a,0)==0;}
 bool endsWith(const char* a)const{return size()>=strlen(a)&&compare(size()-strlen(a),strlen(a),a)==0;}
 String substring(size_t n)const{return substr(n);}
 int indexOf(char c) const {auto i=find(c);return i==npos?-1:int(i);}
};
#define F(s) (s)
constexpr int HEX=16,HTTP_GET=0,HTTP_POST=1;
inline int isDigit(char c){return std::isdigit(static_cast<unsigned char>(c));}
inline uint32_t fakeMillis=1, fakeRand=7;
inline unsigned long millis(){return fakeMillis;}
inline unsigned esp_random(){return ++fakeRand;}
struct FakeChip {uint64_t getEfuseMac()const{return 42;}} inline ESP;
struct FakeWire {void beginTransmission(int){} void write(int){} void write(const uint8_t*,size_t){} int endTransmission(bool=true){return 0;} size_t requestFrom(uint8_t,size_t){return 0;} size_t readBytes(uint8_t*,size_t){return 0;}} inline Wire;
struct FakeSerial {String log;int available(){return 0;} int read(){return -1;} explicit operator bool()const{return true;} template<class... T> void printf(const char* f,T... a){char b[512];snprintf(b,sizeof(b),f,a...);log+=b;} void println(const char* c){log+=c;}} inline Serial;
enum {WIFI_OFF,WIFI_STA,WIFI_AP_STA,WL_DISCONNECTED,WL_CONNECTED};
struct IP {String toString()const{return "192.168.4.1";} bool operator==(const IP&)const{return true;}};
struct FakeWiFi{
 bool sdkPersistent=true, oldLinkStays=false,failAp=false;
 int currentMode=WIFI_OFF,link=WL_DISCONNECTED,starts=0,disconnects=0,sdkWrites=0;
 String ssid, attempted;
 void persistent(bool p){sdkPersistent=p;}
 bool mode(int m){currentMode=m;if(m==WIFI_OFF)link=WL_DISCONNECTED;return true;}
 void setSleep(bool){}
 bool softAP(const char*,const char*){return !failAp;}
 bool softAPdisconnect(bool){return true;}
 IP softAPIP()const{return {};}
 bool disconnect(bool off,bool erase){assert(!erase);++disconnects;if(off)mode(WIFI_OFF);if(!oldLinkStays)link=WL_DISCONNECTED;return true;}
 int begin(const char* s,const char*){++starts;attempted=s;if(sdkPersistent)++sdkWrites;return link;}
 int status()const{return link;}
 String SSID()const{return ssid;}
 void linked(){ssid=attempted;link=WL_CONNECTED;}
} inline WiFi;
struct FakePreferences{
 static inline String bytes;
 static inline bool radio=false,failBytes=false,failRadio=false;
 static inline int saves=0,radioWrites=0,removes=0;
 void begin(const char*,bool){}
 bool getBool(const char* k,bool d){return strcmp(k,"radio")==0?radio:d;}
 size_t putBool(const char* k,bool v){if(strcmp(k,"radio")==0){++radioWrites;if(failRadio)return 0;radio=v;}return 1;}
 size_t getBytes(const char*,void* p,size_t n){if(bytes.size()!=n)return 0;memcpy(p,bytes.data(),n);return n;}
 size_t putBytes(const char*,const void* p,size_t n){++saves;if(failBytes)return 0;bytes.assign((const char*)p,n);return n;}
 String getString(const char*,const char* d){return d;}
 size_t putString(const char*,const String&){return 1;}
 bool remove(const char*){++removes;bytes.clear();return true;}
};
using Preferences=FakePreferences;
struct WebServer{
 static inline WebServer* current=nullptr;
 std::map<int,std::function<void()>> callback;
 std::map<std::string,String> args,headers;
 bool started=false;int code=0;String body,host="192.168.4.1";
 WebServer(int){current=this;}
 struct Client{IP localIP(){return {};}}; Client client(){return {};}
 void on(const char*,int method,std::function<void()> f){callback[method]=std::move(f);}
 String hostHeader(){return host;} String arg(const char* k){return args[k];}
 void begin(){started=true;} void stop(){started=false;} void handleClient(){}
 void sendHeader(const char* h,const char* v){headers[h]=v;}
 void send(int status,const char* =nullptr,const String& s={}){code=status;body=s;}
 void call(int m){assert(started);headers.clear();callback.at(m)();}
};
inline void esp_sntp_set_time_sync_notification_cb(void(*)(timeval*)){}
inline void configTime(int,int,const char*,const char*){}
inline bool updateBusy(){return false;}
inline bool releaseKeyValid(const String&){return false;}
inline void fetchRelease(String,String){}
namespace hardware {
struct Vec{double x,y,z;};
struct Sample {uint32_t uptimeMs;Vec accelG,gyroDps;int16_t accelRaw[3],gyroRaw[3];bool accelOK,gyroOK;int field,reel;};
inline Sample sample(){return {};}
inline bool gyroPower(bool){return false;}
}
