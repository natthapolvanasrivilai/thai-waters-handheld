#include "../WillowCreek/ArrivalPixels.h"
#include "../WillowCreek/Destinations.h"
#include <cstdio>
#include <initializer_list>

int main(){
  arrival::Frame frame{};
  for(int i=0;i<creek::destinationCount;i++){
    for(unsigned age : {720u,1730u,2780u,3500u}){
      arrival::draw(frame,i,creek::destinations[i].pool,age);
      uint32_t hash=2166136261u;
      arrival::raster(frame,[&](int x,int y,uint8_t ink){
        hash=(hash^unsigned((y*240+x)*64+ink))*16777619u;
      });
      std::printf("%d %u %u\n",i,age,hash);
    }
  }
}
