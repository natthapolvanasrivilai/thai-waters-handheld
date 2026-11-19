#pragma once
#include "JournalDisk.h"

namespace creek {
constexpr unsigned catchPageSize=32;
// Fixed little-endian disk format for version 1. UTC is zero when unknown.
struct CatchRecord {
  uint32_t sequence=0, utc=0, grams=0, cupDay=0;
  uint16_t species=0, cm=0;
  uint8_t spot=255, weather=255, period=255, bait=255, flags=0, measurement=3, reserved[2]{};
};
static_assert(sizeof(CatchRecord)==28,"catch archive v1");
enum CatchFlag : uint8_t { TimeKnown=1, LegacyPending=2 };
constexpr const char* archivedMeasures[]={"Total length","Body length","Disc width","Recorded size"};
inline uint8_t archivedMeasure(int id,int cm){
  const char* label=sizeLabel(id,cm);
  for(uint8_t i=0;i<3;i++)if(!strcmp(label,archivedMeasures[i]))return i;
  return 3;
}
enum class CatchStage : uint8_t { Idle, Landed, Acknowledged };
struct CatchTransaction {
  uint32_t magic=0x54435731, priorCount=0;
  CatchRecord record{};
  uint16_t priorBest=0;
  CatchStage stage=CatchStage::Idle;
  uint8_t emptyExtraPage=0;
};
static_assert(sizeof(CatchTransaction)==40,"NVS catch transaction v1");
struct CatchPage {
  uint32_t magic=0x54434c31, index=0, count=0;
  CatchRecord records[catchPageSize]{};
  uint32_t checksum=0;
};
inline uint32_t catchChecksum(const CatchPage& page){
  const auto* bytes=reinterpret_cast<const uint8_t*>(&page);
  uint32_t value=2166136261u;
  for(size_t i=0;i<offsetof(CatchPage,checksum);i++)value=(value^bytes[i])*16777619u;
  return value;
}
inline void catchPageName(char* path,unsigned page,unsigned slot){
  // Seven hex directory-name characters plus prefix fit FAT short names.
  snprintf(path,16,"/C%07lX.%c01",(unsigned long)page,slot?'B':'A');
}
inline DiskRead loadCatchPage(unsigned index,CatchPage& latest,int& slot){
  slot=-1;bool damaged=false;
  for(int i=0;i<2;i++){
    char path[16];catchPageName(path,index,i);
    CatchPage page;
    const auto status=journalDiskRead(path,&page,sizeof(page));
    if(status==DiskRead::Missing)continue;
    if(status!=DiskRead::Good || page.magic!=0x54434c31 || page.index!=index ||
       page.count>catchPageSize || !page.count || page.checksum!=catchChecksum(page)){
      damaged=true;continue;
    }
    if(slot<0 || page.count>latest.count){latest=page;slot=i;}
  }
  return slot>=0?DiskRead::Good:damaged?DiskRead::Invalid:DiskRead::Missing;
}
inline bool archiveCatch(const CatchRecord& record){
  if(!record.sequence || journalDrive(true)!=DiskRead::Good)return false;
  const unsigned n=record.sequence-1,index=n/catchPageSize,position=n%catchPageSize;
  CatchPage page;int slot=-1;
  const auto state=loadCatchPage(index,page,slot);
  // A durable acknowledged transaction for position zero owns a new page.
  // A cut during its first write can leave its only copy truncated.
  if(state!=DiskRead::Good && position)return false;
  if(position<page.count)return memcmp(&record,&page.records[position],sizeof(record))==0;
  if(position!=page.count)return false;
  page.index=index;page.records[page.count++]=record;page.checksum=catchChecksum(page);
  char path[16];catchPageName(path,index,slot==0?1:0);
  if(!journalDiskWrite(path,&page,sizeof(page)))return false;
  CatchPage verify;
  return journalDiskRead(path,&verify,sizeof(verify))==DiskRead::Good && memcmp(&page,&verify,sizeof(page))==0;
}
inline bool readCatch(uint32_t sequence,CatchRecord& record){
  if(!sequence || journalDrive(false)!=DiskRead::Good)return false;
  const unsigned n=sequence-1;CatchPage page;int slot=-1;
  if(loadCatchPage(n/catchPageSize,page,slot)!=DiskRead::Good || n%catchPageSize>=page.count)return false;
  record=page.records[n%catchPageSize];
  return record.sequence==sequence && record.species<fishCount && record.measurement<4 &&
         (record.spot<destinationCount || record.spot==255);
}
inline bool legalTransaction(const CatchTransaction& tx){
  if(tx.magic!=0x54435731)return false;
  if(tx.stage==CatchStage::Idle)return true;
  const auto& r=tx.record;
  return (tx.stage==CatchStage::Landed || tx.stage==CatchStage::Acknowledged) &&
         r.sequence && validSavedSize(r.species,r.cm) && r.measurement<4 && !(r.flags&~(TimeKnown|LegacyPending)) &&
         ((r.utc!=0)==bool(r.flags&TimeKnown)) && (r.spot<destinationCount || r.spot==255) &&
         (r.weather<4 || r.weather==255) && (r.period<4 || r.period==255) && (r.bait<18 || r.bait==255);
}
// Replay the exact target values. A reset after any successful write restarts
// from the acknowledged transaction stored in NVS.
template<class WriteAggregate,class Finish>
bool commitCatch(const CatchTransaction& tx,const Entry& current,WriteAggregate write,Finish finish){
  if(tx.stage!=CatchStage::Acknowledged || !legalTransaction(tx))return false;
  Entry target=current;
  target.count=tx.priorCount==UINT32_MAX?UINT32_MAX:tx.priorCount+1;
  target.best=std::max(tx.priorBest,tx.record.cm);
  const bool already=current.count==target.count && current.best==target.best;
  if(!already && (current.count!=tx.priorCount || current.best!=tx.priorBest))return false;
  if(!archiveCatch(tx.record) || (!already && !write(target)))return false;
  CatchTransaction completed{};completed.record.sequence=tx.record.sequence;
  return finish(completed);
}
}
