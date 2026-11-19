#include "../WillowCreek/RodHidProtocol.h"
#include "../WillowCreek/Creek.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>

static std::vector<int> drain(rodhid::Stream& s,uint32_t from,int slots){
  std::vector<int> keys;
  for(int i=0;i<slots;++i){
    const uint32_t now=from+15*i;
    int k=s.next(now);
    if(k!=rodhid::Stream::idle){s.sent(k,now);keys.push_back(k);}
  }
  return keys;
}
static int signedSteps(int key){
  for(int i=0;i<4;++i){
    if(key==rodhid::Stream::wind[i])return 1<<i;
    if(key==rodhid::Stream::unwind[i])return -(1<<i);
  }
  return 0;
}
int main(){
  using S=rodhid::Stream;
  S s;
  assert(s.next(800)==S::release);
  s.sent(0,800);
  assert(s.next(810)==S::idle);
  assert(s.next(815)==S::heartbeat);
  s.sent(S::heartbeat,815);
  assert(s.next(830)==S::release);
  s.sent(0,830);
  s.sample(0,false,true,0);s.sample(0,true,false,1);
  auto k=drain(s,845,8);
  assert((k==std::vector<int>{S::lift,0,S::cast,0,0x26,0}));
  for(int reverse:{0,1}){
    S encoder;
    creek::Wheel wheel;
    int net=0,last=0,presses=0,pitchCount=0;
    for(int i=0;i<110;i++){
      uint32_t now=uint32_t(i)*15;
      int raw=(i<65?i*64:4096)%4096;
      const float turns=wheel.read(raw,true,now,reverse);
      encoder.sample(turns,false,false,.5f);
      int key=encoder.next(now);
      if(key>=0){
        if(key){assert(last==0);++presses;}
        if(key==0x22)++pitchCount;
        net+=signedSteps(key);encoder.sent(key,now);last=key;
      }
    }
    assert(net==(reverse?-24:24));assert(presses>12 && pitchCount>=2);
  }
  S queue;
  queue.sample(1,0,0,NAN);queue.sample(-1,0,0,NAN);assert(queue.counts==0);
  queue.sample(5,0,0,NAN);assert(queue.counts==24*4096);
  auto old=drain(queue,0xfffffff0u,20);
  int n=0;for(int key:old)n+=signedSteps(key);assert(n==24);
  // Re-arm starts with neutral, a heartbeat and no twist from the old connection.
  queue={};auto reset=drain(queue,51,5);
  assert((reset==std::vector<int>{0,S::heartbeat,0}));
  S quant;
  quant.sample(0,0,0,.50f);assert(quant.pitch==4);
  quant.sample(0,0,0,.57f);assert(quant.pitch==4);
  quant.sample(0,0,0,.59f);assert(quant.pitch==5);
  quant.sample(0,0,0,NAN);assert(quant.pitch==5);
  std::puts("PASS Rod HID v1: gesture FIFO, wrap, signed encoder +/-24, pitch, heartbeat, neutral and reconnect");
}
