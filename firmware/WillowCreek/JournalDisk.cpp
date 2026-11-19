#include "JournalDisk.h"
#include <FFat.h>
#include <Preferences.h>
#include <esp_partition.h>

namespace creek {
DiskRead journalDrive(bool initializeBlank){
 static bool mounted=false,checked=false,blank=false;
 if(mounted)return DiskRead::Good;
 if(!checked){
   const auto* partition=esp_partition_find_first(ESP_PARTITION_TYPE_DATA,ESP_PARTITION_SUBTYPE_DATA_FAT,"ffat");
   if(!partition)return DiskRead::Invalid;
   // Check before a first wear-level mount can initialize metadata on erased flash.
   uint8_t data[1024];blank=true;
   for(size_t offset=0;blank && offset<partition->size;offset+=sizeof(data)){
     const size_t count=std::min(sizeof(data),size_t(partition->size-offset));
     if(esp_partition_read(partition,offset,data,count)!=ESP_OK)return DiskRead::Invalid;
     blank=std::all_of(data,data+count,[](uint8_t b){return b==0xff;});
   }
   checked=true;
 }
 if(blank && !initializeBlank)return DiskRead::Missing;
 Preferences init;
 if(!init.begin("atlas-storage",false))return DiskRead::Invalid;
 bool pending=init.getBool("format-new",false);
 if(blank && !pending){
   // Recover a power interruption during first-time provisioning.
   if(!init.putBool("format-new",true))return DiskRead::Invalid;
   pending=true;
 }
 const bool ok=FFat.begin(pending,"/ffat",2);
 if(!ok)return DiskRead::Invalid;
 if(pending && !init.putBool("format-new",false)){FFat.end();return DiskRead::Invalid;}
 mounted=true;blank=false;return DiskRead::Good;
}
DiskRead journalDiskRead(const char* path,void* data,size_t bytes){
 auto file=FFat.open(path,FILE_READ);
 if(!file)return FFat.exists(path)?DiskRead::Invalid:DiskRead::Missing;
 return file.size()==bytes && file.read(static_cast<uint8_t*>(data),bytes)==bytes?DiskRead::Good:DiskRead::Invalid;
}
bool journalDiskWrite(const char* path,const void* data,size_t bytes){
 auto file=FFat.open(path,FILE_WRITE);
 if(!file)return false;
 const bool ok=file.write(static_cast<const uint8_t*>(data),bytes)==bytes;
 file.flush();file.close();return ok;
}
}
