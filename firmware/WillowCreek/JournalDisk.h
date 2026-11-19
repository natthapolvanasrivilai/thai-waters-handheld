#pragma once
#include "Waters.h"
#include <cstdio>
#include <cstddef>
#include <cstring>

namespace creek {
enum class DiskRead { Missing, Invalid, Good };
DiskRead journalDrive(bool initializeBlank);
DiskRead journalDiskRead(const char* path,void* data,size_t bytes);
bool journalDiskWrite(const char* path,const void* data,size_t bytes);

// The original 52 entries and ranks keep their existing NVS key and byte format.
// Extended IDs occupy 32-entry pages on the board's existing FAT data partition.
constexpr int journalPageEntries=32;
struct JournalSector {
 uint32_t magic=0x544a5031u,page=0,generation=0;
 Entry entries[journalPageEntries]{};
 uint32_t checksum=0;
};
inline uint32_t sectorChecksum(const JournalSector& page){
 uint32_t hash=2166136261u;
 const auto* bytes=reinterpret_cast<const uint8_t*>(&page);
 for(size_t i=0;i<offsetof(JournalSector,checksum);++i)hash=(hash^bytes[i])*16777619u;
 return hash;
}
inline void sectorName(char* name,size_t size,int page,int slot){
 snprintf(name,size,"/TW%04X%c.BIN",page,slot?'B':'A');
}
inline DiskRead loadSector(int index,JournalSector& out,int& active){
 JournalSector candidate;active=-1;bool damaged=false;
 for(int slot=0;slot<2;++slot){
   char name[16];sectorName(name,sizeof(name),index,slot);
   const auto read=journalDiskRead(name,&candidate,sizeof(candidate));
   if(read==DiskRead::Missing)continue;
   if(read!=DiskRead::Good || candidate.magic!=0x544a5031u || candidate.page!=uint32_t(index) ||
      candidate.checksum!=sectorChecksum(candidate)){damaged=true;continue;}
   if(active<0 || int32_t(candidate.generation-out.generation)>0){out=candidate;active=slot;}
 }
 return active>=0?DiskRead::Good:damaged?DiskRead::Invalid:DiskRead::Missing;
}
inline bool restoreExtraBook(Journal& journal){
 const auto drive=journalDrive(false);
 if(drive!=DiskRead::Good)return drive==DiskRead::Missing;
 bool valid=true;
 for(int start=originalSpecies;start<fishCount;start+=journalPageEntries){
   JournalSector page;int active;
   const auto read=loadSector((start-originalSpecies)/journalPageEntries,page,active);
   if(read==DiskRead::Invalid)valid=false;
   if(read==DiskRead::Good){
     const int count=std::min(journalPageEntries,fishCount-start);
     std::copy(page.entries,page.entries+count,journal.entries+start);
   }
 }
 return valid;
}
inline bool saveExtraEntry(int id,const Entry& entry,bool recoverEmptyPage=false){
 if(id<originalSpecies || id>=fishCount || journalDrive(true)!=DiskRead::Good)return false;
 const int index=(id-originalSpecies)/journalPageEntries;
 JournalSector page;int active;
 if(loadSector(index,page,active)==DiskRead::Invalid && !recoverEmptyPage)return false;
 auto& prior=page.entries[(id-originalSpecies)%journalPageEntries];
 if(prior.count==entry.count && prior.best==entry.best)return true;
 if(entry.count!=prior.count+1 || prior.best>entry.best)return false;
 page.page=index;++page.generation;prior=entry;
 page.checksum=sectorChecksum(page);
 char name[16];sectorName(name,sizeof(name),index,active==0?1:0);
 if(!journalDiskWrite(name,&page,sizeof(page)))return false;
 JournalSector written;
 return journalDiskRead(name,&written,sizeof(written))==DiskRead::Good &&
        memcmp(&written,&page,sizeof(written))==0;
}
}
