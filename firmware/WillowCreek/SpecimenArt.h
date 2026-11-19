#pragma once
#include "FieldPlates.h"
#include "SpecimenAvailability.h"
namespace specimen {
inline int pixel(const Frame& f,int x,int y){
 x-=f.x;y-=f.y;if(unsigned(x)>=f.w||unsigned(y)>=f.h)return 0;
 const uint32_t offset=f.offset+y*((f.w+1)/2)+x/2;
 const int pair=offset<residentBytes?packed[offset]:cardPixels[offset-residentBytes];
 return x&1?pair&15:pair>>4;
}
}
