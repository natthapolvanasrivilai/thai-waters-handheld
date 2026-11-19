#pragma once
#include "FieldPlates.h"
namespace specimen {
inline bool has(int id){return id>=0&&id<int(sizeof(index)/sizeof(index[0]))&&(id<60||index[id]>=0);}
inline int pixel(const Frame& f,int x,int y){
 x-=f.x;y-=f.y;if(unsigned(x)>=f.w||unsigned(y)>=f.h)return 0;
 const int pair=packed[f.offset+y*((f.w+1)/2)+x/2];
 return x&1?pair&15:pair>>4;
}
}
