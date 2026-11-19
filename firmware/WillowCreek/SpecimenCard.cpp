#include "SpecimenAvailability.h"
#ifdef ARDUINO
#include <Arduino.h>
#include <SD_MMC.h>
#include <esp_heap_caps.h>
#include <mbedtls/sha256.h>
#include <algorithm>
#include <cstring>

namespace specimen {
void loadCardArt(){
 if(!cardBytes||cardPixels)return;
 // Waveshare 31137 onboard TF slot, wired for one-bit SDMMC. Mount read-only
 // in practice: no game path writes, initializes, or formats a card.
 if(!SD_MMC.setPins(11,10,9)||!SD_MMC.begin("/sdcard",true,false,20000)){
   Serial.println("Field art: card unavailable; resident collection active");return;
 }
 auto file=SD_MMC.open("/TW-FISH.BIN",FILE_READ);
 uint8_t* buffer=nullptr;
 if(file&&file.size()==cardBytes)
   buffer=static_cast<uint8_t*>(heap_caps_malloc(cardBytes,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT));
 bool valid=buffer!=nullptr;
 for(size_t n=0;valid&&n<cardBytes;){
   const size_t chunk=std::min(size_t(32768),size_t(cardBytes-n));
   valid=file.read(buffer+n,chunk)==chunk;
   n+=chunk;yield();
 }
 uint8_t actual[32];
 if(valid)valid=mbedtls_sha256(buffer,cardBytes,actual,0)==0&&!memcmp(actual,cardDigest,sizeof(actual));
 file.close();SD_MMC.end();
 if(valid)cardPixels=buffer;else free(buffer);
 Serial.println(valid?"Field art: verified and loaded":"Field art: incompatible or unreadable; resident collection active");
}
}
#endif
