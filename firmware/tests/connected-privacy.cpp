#include "FakeConnected.h"
#include "Connected.h"
#include <iostream>
void printCatchRecord(uint32_t){}
using P=FakePreferences;

static void step(unsigned dt=10){fakeMillis+=dt;tickConnected();}
static WebServer& form(){
 startPairing();
 auto& web=*WebServer::current;
 web.call(HTTP_GET);
 assert(web.code==200&&web.headers["Cache-Control"]=="no-store");
 assert(web.body.find("type=password")!=String::npos);
 const auto choose=web.body.find("name=r");
 assert(choose!=String::npos&&"Remember opt-in control must exist");
 const auto tag=web.body.substr(web.body.rfind('<',choose),web.body.find('>',choose)-web.body.rfind('<',choose));
 assert(tag.find("type=checkbox")!=String::npos&&tag.find("checked")==String::npos);
 return web;
}
static void post(WebServer& web,const char* s,const char* p,const char* remember="",const char* forcedToken=nullptr){
 const auto i=web.body.find("name=t value='");assert(i!=String::npos);
 const auto begin=i+strlen("name=t value='");
 const auto token=web.body.substr(begin,web.body.find('\'',begin)-begin);
 web.args={{"s",s},{"p",p},{"r",remember},{"t",forcedToken?forcedToken:token}};
 web.call(HTTP_POST);
 assert(web.body.find(p)==String::npos);
 assert(Serial.log.find(p)==String::npos);
}
int main(int argc,char** argv){
 assert(argc==2);const std::string which=argv[1];
 if(which=="previous"||which=="same-ssid"||which=="previous-remember"){
  P::bytes=String(98,'\0');P::bytes.replace(0,8,"Old-WiFi");P::bytes.replace(33,9,"oldphrasE");P::radio=true;
 }
 beginConnected();assert(!WiFi.sdkPersistent && WiFi.sdkWrites==0);
 if(P::radio)WiFi.linked();
 const String original=P::bytes;
 if(which=="ap-fails"){
   WiFi.failAp=true;startPairing();
   assert(!radioEnabled()&&!WebServer::current->started&&WiFi.currentMode==WIFI_OFF);
   return 0;
 }
 auto& web=form();
 if(which=="bad-token"||which=="bad-host"){
   if(which=="bad-host")web.host="wrong";
   post(web,"Example","dummyPass1","1",which=="bad-token"?"wrong":nullptr);
   assert(web.code==403&&P::saves==0&&web.headers["Cache-Control"]=="no-store");
   return 0;
 }
 const bool old=which=="previous"||which=="previous-remember"||which=="same-ssid";
 const auto remember=which=="remember"||which=="write-fails"||which=="radio-write-fails"||which=="expired"||which=="same-ssid"||which=="previous-remember";
 if(which=="same-ssid")WiFi.oldLinkStays=true;
 const int before=WiFi.starts;
 post(web,which=="same-ssid"?"Old-WiFi":"Example","dummyPass1",remember?"1":which=="invalid-opt"?"on":"");
 assert(web.code==200);
 assert(web.headers["Cache-Control"]=="no-store");
 if(which=="same-ssid"){step();assert(WiFi.starts==before&&P::saves==0&&web.started);WiFi.oldLinkStays=false;WiFi.link=WL_DISCONNECTED;}
 step();assert(WiFi.starts==before+1 && P::saves==0);
 if(which=="expired"){
  WiFi.linked();step(300001);assert(P::saves==0&&!web.started&&!radioEnabled());return 0;
 }
 if(which=="timeout"){
  step(18001);assert(P::saves==0&&web.started&&strstr(networkStatus(),"failed"));stopPairing();
  assert(!radioEnabled()&&!web.started);return 0;
 }
 if(which=="cancel"){
  stopPairing();WiFi.linked();step();
  assert(P::saves==0&&!web.started&&!radioEnabled());
  return 0;
 }
 if(which=="write-fails")P::failBytes=true;
 if(which=="radio-write-fails")P::failRadio=true;
 WiFi.linked();step();
 assert(!web.started&&radioEnabled()&&WiFi.link==WL_CONNECTED);
 assert(WiFi.starts==before+1 && "do not reconnect over a successful session");
 assert(WiFi.sdkWrites==0&&P::removes==0);
 assert(strstr(networkStatus(),"connected"));
 if(old||!remember){
  assert(P::saves==0&&P::radioWrites==0&&P::bytes==original);
  if(!remember)assert(strstr(networkStatus(),"for this session"));
 }else {
  assert(P::saves==1);
  if(which=="write-fails")assert(P::bytes.empty()&&P::radioWrites==0&&strstr(networkStatus(),"not saved"));
  else if(which=="radio-write-fails")
   assert(P::bytes.find("Example")!=String::npos&&!P::radio&&strstr(networkStatus(),"auto-join not saved"));
  else assert(P::bytes.find("Example")!=String::npos&&P::radio);
 }
 WiFi.link=WL_DISCONNECTED;assert(!strstr(networkStatus(),"Wi-Fi connected"));
 std::cout<<"PASS "<<which<<'\n';
}
