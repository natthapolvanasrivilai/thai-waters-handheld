#include "UpdateFeed.h"
#include "Connected.h"
#include <esp_http_client.h>
#include <esp_crt_bundle.h>
#include <esp_ota_ops.h>
#include <mbedtls/pk.h>
#include <mbedtls/sha256.h>
#include <atomic>
#include <cstring>

namespace {
std::atomic<const char*> report{"Updates ready for USB owner setup"};
std::atomic<bool> busy{false};
String feed,publicKey;
int digit(char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:c>='A'&&c<='F'?c-'A'+10:-1;}
bool parseKey(const String& hex,mbedtls_pk_context& key){
  if(hex.length()!=182)return false;
  uint8_t der[91];
  for(int i=0;i<91;i++){
    int a=digit(hex[2*i]),b=digit(hex[2*i+1]);if(a<0||b<0)return false;der[i]=16*a+b;
  }
  return mbedtls_pk_parse_public_key(&key,der,sizeof(der))==0 && mbedtls_pk_can_do(&key,MBEDTLS_PK_ECDSA) && mbedtls_pk_get_bitlen(&key)==256;
}
bool exact(esp_http_client_handle_t h,uint8_t* dst,size_t n){
  while(n){int k=esp_http_client_read(h,(char*)dst,n);if(k<=0)return false;dst+=k;n-=k;}return true;
}
uint32_t read32(const uint8_t* p){return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);}
const char* download(esp_http_client_handle_t h){
  if(esp_http_client_open(h,0)!=ESP_OK)return "Could not connect to release server";
  int64_t total=esp_http_client_fetch_headers(h);
  if(esp_http_client_get_status_code(h)!=200)return "Release feed unavailable";
  uint8_t head[52],sl[2],sig[80],digest[32];
  if(!exact(h,head,sizeof(head))||memcmp(head,"TWOTA001",8)||read32(head+8)!=productModel)return "Wrong model or release format";
  uint32_t version=read32(head+12),size=read32(head+16);
  auto slot=esp_ota_get_next_update_partition(nullptr);
  if(!slot||!size||size>slot->size||!exact(h,sl,2))return "Image does not fit this board";
  size_t n=sl[0]+256u*sl[1];
  if(n<8||n>sizeof(sig)||!exact(h,sig,n)||(total>=0&&total!=int64_t(sizeof(head)+2+n+size)))return "Invalid release length";
  mbedtls_pk_context key;mbedtls_pk_init(&key);
  bool ok=parseKey(publicKey,key)&&!mbedtls_sha256(head,sizeof(head),digest,0)&&!mbedtls_pk_verify(&key,MBEDTLS_MD_SHA256,digest,32,sig,n);mbedtls_pk_free(&key);
  if(!ok)return "Release signature rejected";
  if(version<=releaseNumber)return "Already current or older release";
  esp_ota_handle_t ota;
  if(esp_ota_begin(slot,size,&ota)!=ESP_OK)return "Could not open inactive slot";
  mbedtls_sha256_context hash;mbedtls_sha256_init(&hash);ok=!mbedtls_sha256_starts(&hash,0);
  uint8_t buf[2048];report.store("Downloading to inactive slot");
  for(uint32_t left=size;ok&&left;){
    size_t part=std::min<size_t>(left,sizeof(buf));ok=exact(h,buf,part)&&!mbedtls_sha256_update(&hash,buf,part)&&esp_ota_write(ota,buf,part)==ESP_OK;left-=part;
  }
  ok=ok&&!mbedtls_sha256_finish(&hash,digest)&&!memcmp(digest,head+20,32);mbedtls_sha256_free(&hash);
  if(!ok){esp_ota_abort(ota);return "Incomplete or corrupt release";}
  if(esp_ota_end(ota)!=ESP_OK||esp_ota_set_boot_partition(slot)!=ESP_OK)return "Firmware validation failed";
  return nullptr;
}
void worker(void*){
  esp_http_client_config_t cfg{};cfg.url=feed.c_str();cfg.crt_bundle_attach=esp_crt_bundle_attach;
  cfg.transport_type=HTTP_TRANSPORT_OVER_SSL;cfg.timeout_ms=10000;cfg.disable_auto_redirect=true;
  auto client=esp_http_client_init(&cfg);
  const char* result=client?download(client):"Could not start HTTPS";
  if(client)esp_http_client_cleanup(client);
  if(result){report.store(result);busy.store(false);}
  else {report.store("Verified. Restarting...");delay(1000);ESP.restart();}
  vTaskDelete(nullptr);
}
}
bool releaseKeyValid(const String& hex){mbedtls_pk_context key;mbedtls_pk_init(&key);bool ok=parseKey(hex,key);mbedtls_pk_free(&key);return ok;}
bool updateBusy(){return busy.load();}
const char* updateStatus(){return report.load();}
void fetchRelease(String url,String key){
  if(busy.load())return;
  if(!url.startsWith("https://")||!releaseKeyValid(key)){report.store("Set owner key and HTTPS feed over USB");return;}
  busy.store(true);feed=url;publicKey=key;report.store("Checking signed release...");
  if(xTaskCreate(worker,"release",12288,nullptr,1,nullptr)!=pdPASS){busy.store(false);report.store("Insufficient update memory");}
}
extern "C" bool verifyRollbackLater(){return true;}
void confirmUpdateHealth(bool healthy){
  esp_ota_img_states_t state;
  if(esp_ota_get_state_partition(esp_ota_get_running_partition(),&state)==ESP_OK&&state==ESP_OTA_IMG_PENDING_VERIFY){
    if(healthy)esp_ota_mark_app_valid_cancel_rollback();else esp_ota_mark_app_invalid_rollback_and_reboot();
  }
}

