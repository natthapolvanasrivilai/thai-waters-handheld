#pragma once
#include "Arrival.h"

namespace arrival {
// Space in each stamp is transparent. Bunched leaf highlights and interlocking
// dark lobes keep an irregular edge even against a brightly lit sky.
constexpr const char* canopy[]={
 "        .+++.            ","     .++ll+++.+.         ",
 "   .+lllLLll+++l+.       ","  .++lLLLLlll+lLl++.     ",
 " .+LLLlll++llLLLl+++.    ",".lLLll++..+lLll++lLl++.  ",
 ".+lll+:::+lll+++lllLl++. "," .+:+++lLLLll+::+llll++. ",
 "  .::+LLll+++:+::::+++:. ","   .++l+++:::::++++:::.  ",
 "    .:::+:.:++ll+++:.    ","      .::.  .:++:::.     ",
 "        .     .::.       "
};
constexpr const char* reeds[]={
 "       l      +   ","   +   l  l  +    ","   l   +l l +   l ",
 " l  l  +l ++  ll  ","  l l  +l l+ ll   ","   ll+ l+:l+l+  + ",
 " +   l+++l:l++ll  ","  +ll++:+l+++l    ","   ++l+::+:++  l  ",
 "    .++:++::+ll   ","     .::::::+     ","       .:::.      "
};
inline uint8_t leaf(char c){
  switch(c){case '.':return scenery::Wood;case ':':return scenery::Crown;
    case '+':return 63;case 'l':return scenery::Leaf;case 'L':return scenery::SunLeaf;default:return 255;}
}
inline void span(uint8_t* row,int x,int u,int ink){
  x=scenery::maxOf(0,x);u=scenery::minOf(239,u);
  for(;x<=u;++x)row[x]=uint8_t(ink);
}
inline void stripe(const Shape& s,int y,uint8_t* row){
  const int x=s.x/2,top=s.y/2,u=s.u/2,bot=s.v/2;
  if(s.kind==Sprite){
    if(y<top||y>=bot||u<=x)return;
    const bool tree=s.ink==Broadleaf;
    const int h=tree?13:12,w=tree?25:18;
    const char* pixels=tree?canopy[(y-top)*h/(bot-top)]:reeds[(y-top)*h/(bot-top)];
    for(int col=scenery::maxOf(0,x);col<scenery::minOf(240,u);++col){
      uint8_t k=leaf(pixels[(col-x)*w/(u-x)]);
      if(k!=255)row[col]=k;
    }
    return;
  }
  if(s.kind==Line){
    if(y<scenery::minOf(top,bot)||y>scenery::maxOf(top,bot))return;
    if(top==bot){span(row,scenery::minOf(x,u),scenery::maxOf(x,u),s.ink);return;}
    const float dx=float(u-x)/(bot-top);
    float a=x+(y-top)*dx,b=a+(dx<0?-dx:dx)*.5f;
    a-=((dx<0?-dx:dx)*.5f);
    span(row,scenery::maxOf(scenery::minOf(x,u),int(a+.5f)),scenery::minOf(scenery::maxOf(x,u),int(b+.5f)),s.ink);
    return;
  }
  int xs[]={x,u,s.a/2},ys[]={top,bot,s.b/2};
  int lo=30000,hi=-30000;
  for(int i=0;i<3;i++){
    const int j=(i+1)%3;
    if(y<scenery::minOf(ys[i],ys[j])||y>scenery::maxOf(ys[i],ys[j]))continue;
    if(ys[i]==ys[j]){lo=scenery::minOf(lo,scenery::minOf(xs[i],xs[j]));hi=scenery::maxOf(hi,scenery::maxOf(xs[i],xs[j]));}
    else{int hit=xs[i]+(y-ys[i])*(xs[j]-xs[i])/(ys[j]-ys[i]);lo=scenery::minOf(lo,hit);hi=scenery::maxOf(hi,hit);}
  }
  span(row,lo,hi,s.ink);
}
inline unsigned patch(int x,int z,unsigned seed){
  return scenery::hash(unsigned(x)*0x9e3779b1u+unsigned(z)*0x85ebca77u+seed);
}
inline int material(int kind,int x,int z,unsigned seed){
  using namespace scenery;
  const unsigned cell=patch(x>>3,z>>3,seed);
  // Place an irregular cluster inside each eight-texel cell. The two rows
  // of a pebble share their shape and take different light from the sky.
  const int dx=(x&7)-int(cell&7), dz=(z&7)-int(cell>>3&7);
  bool fleck=dz==0&&dx>=0&&dx<=int(1+(cell>>7&3));
  bool edge=dz==1&&dx>=1&&dx<=2;
  switch(kind){
    case Grass:
      if((dx==dz||dx==1)&&dz>=-2&&dz<=1)return cell&256?Leaf:58;
      return (cell%7==0&&dx<1&&dz>=0)?Wood:Reed;
    case Earth:
      if(fleck)return cell&64?57:StoneLight;
      if(edge)return Timber;
      return (cell%5==0&&dx>=0&&dz>0)?57:Sand;
    case Gravel:
      if(fleck)return cell&64?StoneLight:Stone;
      if(edge)return Wood;
      return cell%3==0&&dx<1?60:Timber;
    case Asphalt:return fleck||edge?59:Stone;
    case Gunwale:
      if(((z+(x>>4))&7)==0 && (x&15)<11)return 60;
      return fleck?Timber:61;
    default:return fleck?62:Post;
  }
}
// A fixed 8x8 threshold pattern hands the view to the destination already
// behind this layer, without storing a second LCD image or temporal noise.
inline unsigned revealRank(int x,int y){
  constexpr unsigned b[]={0,2,3,1};
  return b[(x&1)+2*(y&1)]*16+b[(x>>1&1)+2*(y>>1&1)]*4+b[(x>>2&1)+2*(y>>2&1)];
}
template<class Output> inline void raster(const Frame& f,Output output){
  if(!f.count||f.reveal>=64)return;
  uint8_t row[scenery::width];
  for(int y=0;y<scenery::height;y++){
    for(auto& px:row)px=255;
    for(int i=0;i<f.count;i++)stripe(f.shapes[i],y,row);
    const float dy=2*y+1-f.horizon;
    const float depth=dy>1?175*f.eye/dy:22.f;
    // 32 world texels per metre. Integer stepping keeps grain fixed to the
    // bank while its apparent scale changes as the eye moves along the trail.
    const int step=int(depth*(2*32*256.f/175));
    int earthX=int(((-f.center*depth/175)-f.bend*depth*depth*.002f)*32*256);
    int earthZ=int((depth+f.distance)*32);
    for(int x=0;x<scenery::width;x++,earthX+=step){
      int k=row[x];if(k==255||(f.reveal&&revealRank(x,y)<f.reveal))continue;
      if(k>=Grass){
        if(k==Gunwale||k==Dashboard)k=material(k,x-int(f.boatShift/2),y-int(f.boatDrop/2),f.seed);
        else k=material(k,earthX>>8,earthZ,f.seed);
      }
      output(x,y,uint8_t(k));
    }
  }
}
}
