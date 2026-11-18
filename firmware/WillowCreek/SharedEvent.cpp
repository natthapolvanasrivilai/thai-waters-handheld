#include "Connected.h"
#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_system.h>
#include <cstdio>
namespace {
WiFiUDP udp;
bool enabled=false,bound=false;
uint32_t token=0,roundId=0,lastSend=0,lastReply=0,score=0;
int at=-1;
char message[54]="Off - tap to join";
}
bool eventActive(){return enabled;}
const char* eventStatus(){return message;}
void toggleEvent(){
 enabled=!enabled;udp.stop();bound=false;roundId=score=lastReply=0;at=-1;
 if(enabled){token=esp_random()|1u;snprintf(message,sizeof(message),"Looking for LAN host");}
 else snprintf(message,sizeof(message),"Off - tap to join");
}
void eventCatch(){if(enabled&&roundId&&millis()-lastReply<4500)++score;}
void eventTick(int site){
 if(!enabled)return;
 if(at!=site){at=site;score=roundId=lastReply=0;}
 if(WiFi.status()!=WL_CONNECTED){snprintf(message,sizeof(message),"Join Wi-Fi to enter");return;}
 if(!bound)bound=udp.begin(0);
 uint32_t now=millis();
 if(now-lastSend>=950){
  lastSend=now;char packet[100];snprintf(packet,sizeof(packet),"TW1 %lu %u %lu %lu",(unsigned long)token,unsigned(site),(unsigned long)roundId,(unsigned long)score);
  IPAddress mask=WiFi.subnetMask(),address=WiFi.localIP();for(int i=0;i<4;i++)address[i]|=uint8_t(~mask[i]);
  if(udp.beginPacket(address,42438)){udp.write((uint8_t*)packet,strlen(packet));udp.endPacket();}
 }
 int length=udp.parsePacket();if(length>0&&length<120){
  char b[120];int n=udp.read(b,sizeof(b)-1);if(n<=0)return;b[n]=0;
  unsigned long who,round;unsigned spot,seconds,players,total;
  if(sscanf(b,"TW1R %lu %u %lu %u %u %u",&who,&spot,&round,&seconds,&players,&total)==6&&who==token&&spot==unsigned(site)&&round&&seconds<=180){
   if(round!=roundId){roundId=round;score=0;}lastReply=now;
   snprintf(message,sizeof(message),"%u anglers  %us  %u/8 caught",players,seconds,total);
  }
 }else if(length>0)udp.clear();
 if(!lastReply||now-lastReply>4500)snprintf(message,sizeof(message),"Looking for LAN event host");
}

