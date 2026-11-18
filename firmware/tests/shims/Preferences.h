#pragma once
#include <map>
#include <string>
#include <vector>
#include <cstring>
class Preferences {
 std::map<std::string,std::vector<uint8_t>> data;
public:
 void begin(const char*,bool){}
 size_t getBytesLength(const char* k){return data[k].size();}
 size_t putBytes(const char* k,const void* src,size_t n){auto p=(const uint8_t*)src;data[k]={p,p+n};return n;}
 size_t getBytes(const char* k,void* dst,size_t n){auto& val=data[k];if(val.size()!=n)return 0;memcpy(dst,val.data(),n);return n;}
 uint8_t getUChar(const char* k,uint8_t def){return data[k].size()==1?data[k][0]:def;}
 size_t putUChar(const char* k,uint8_t v){return putBytes(k,&v,1);}
 bool getBool(const char* k,bool def){return getUChar(k,def)!=0;}
 size_t putBool(const char* k,bool v){return putUChar(k,v);}
};
