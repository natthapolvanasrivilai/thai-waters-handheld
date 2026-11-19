#include "Connected.h"
#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_system.h>
#include <cstdio>
#include <Preferences.h>
#include "Bait.h"
#include "Destinations.h"
namespace {
WiFiUDP udp;
bool enabled=false,bound=false;
uint32_t token=0,roundId=0,lastSend=0,lastReply=0,score=0;
int at=-1,cupSpot=-1,cupSpecies=-1,cupMin=0,entryCm=0;
unsigned cupDay=0,entryDay=0;
char goalText[110]="",rankText[80]="",baitText[64]="";
char message[54]="Off - tap to join";
}
const char* cupGoal(){return goalText;}
const char* cupBait(){return baitText;}
const char* cupStanding(){return rankText;}
unsigned eventDay(){return enabled?cupDay:0;}
bool eventActive(){return enabled;}
const char* eventStatus(){return message;}
void toggleEvent(){
 enabled=!enabled;udp.stop();bound=false;roundId=score=lastReply=0;at=-1;
 cupDay=entryDay=0;entryCm=0;goalText[0]=rankText[0]=baitText[0]=0;
 if(enabled){Preferences identity;identity.begin("cup-angler",false);
 token=identity.getUInt("alias",0);
 if(!token){token=esp_random()|1u;identity.putUInt("alias",token);}
 identity.end();snprintf(message,sizeof(message),"Looking for LAN host");}
 else snprintf(message,sizeof(message),"Off - tap to join");
}
void eventCatch(int spot,int species,int cm,unsigned landedDay){
 if(enabled&&roundId&&millis()-lastReply<4500)++score;
 if(enabled&&landedDay && landedDay==cupDay && spot==cupSpot && species==cupSpecies && cm>=cupMin){
   entryDay=cupDay;entryCm=std::max(entryCm,cm);
 }
}
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
  snprintf(packet,sizeof(packet),"TWC1 %lu %u %u %u %u",(unsigned long)token,
    unsigned(entryCm?cupSpot:site),entryDay,unsigned(entryCm?cupSpecies:0),unsigned(entryCm));
  if(udp.beginPacket(address,42438)){udp.write((uint8_t*)packet,strlen(packet));udp.endPacket();}
 }
 int length=udp.parsePacket();if(length>0&&length<120){
  char b[120];int n=udp.read(b,sizeof(b)-1);if(n<=0)return;b[n]=0;
  unsigned long who,round;unsigned spot,seconds,players,total;
  unsigned day,fish,min,rank,best,lead;
  if(sscanf(b,"TWCR %lu %u %u %u %u %u %u %u",&who,&day,&spot,&fish,&min,&rank,&best,&lead)==8 &&
     who==token && spot<creek::destinationCount && fish<creek::fishCount && min<=unsigned(creek::catalog[fish].high)){
    if(day!=cupDay || best>=unsigned(entryCm)){entryCm=0;entryDay=0;}
    cupDay=day;cupSpot=spot;cupSpecies=fish;cupMin=min;
    snprintf(goalText,sizeof(goalText),"%s: %s %u+ cm %s",creek::destinations[spot].name,creek::catalog[fish].name,min,creek::sizeLabel(fish,min));
    const int bait=creek::preferredChoice(fish);
    snprintf(baitText,sizeof(baitText),"Cup bait: %s / %s",creek::baitNames[bait%6],creek::depthNames[bait/6]);
    if(rank)snprintf(rankText,sizeof(rankText),"Daily cup #%u: %u cm / leader %u cm",rank,best,lead);
    else snprintf(rankText,sizeof(rankText),"Daily cup: unranked / leader %u cm",lead);
  }
  if(sscanf(b,"TW1R %lu %u %lu %u %u %u",&who,&spot,&round,&seconds,&players,&total)==6&&who==token&&spot==unsigned(site)&&round&&seconds<=180){
   if(round!=roundId){roundId=round;score=0;}lastReply=now;
   snprintf(message,sizeof(message),"%u anglers  %us  %u/8 caught",players,seconds,total);
  }
 }else if(length>0)udp.clear();
 if(!lastReply||now-lastReply>4500)snprintf(message,sizeof(message),"Looking for LAN event host");
}

