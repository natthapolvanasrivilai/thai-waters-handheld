#pragma once
#include "ScenicRecipes.h"

namespace scenery {
constexpr int width=240, height=160, colorCount=64;
using Color=uint32_t;
enum Ink { Sky=0, Cloud=8, Sun=12, Glow=13, WaterTop=14, WaterLight=22, Far=26,
  Mist=27, Ridge=28, Wood=29, Crown=30, Leaf=31, SunLeaf=32, Shadow=33,
  Reed=34, Tip=35, Sand=36, Stone=37, StoneLight=38, Deep=39, Post=40, Timber=41,
  Roof=42, Wall=43, Window=44, Gold=45, Canvas=46, Petal=47, Wake=48, Star=49 };
inline int maxOf(int a,int b){return a>b?a:b;}
inline int minOf(int a,int b){return a<b?a:b;}
inline int clamp(int a,int lo,int hi){return maxOf(lo,minOf(hi,a));}
inline unsigned hash(unsigned v){
  v^=v>>16;v*=0x7feb352dU;v^=v>>15;v*=0x846ca68bU;return v^(v>>16);
}
struct Random {
  unsigned state;
  unsigned next(){state=state*1664525U+1013904223U;return state>>8;}
  int between(int lo,int hi){return lo+next()%unsigned(hi-lo+1);}
};
inline Color mix(Color a,Color b,int amount){
  Color out=0;
  for(int shift=0;shift<=16;shift+=8){
    int x=(a>>shift)&255,y=(b>>shift)&255;
    out|=unsigned((x*(255-amount)+y*amount)/255)<<shift;
  }
  return out;
}
inline void ramp(Color *p,int first,int last,Color a,Color b){
  for(int i=first;i<=last;i++)p[i]=mix(a,b,(i-first)*255/(last-first));
}
struct Light {
  Color sky, horizon, clouds, sun, water, nearWater, fog, canopy, shade, highlight;
};
constexpr Light lights[]={
  {0x929ab4,0xf7caa3,0xeebeb1,0xffdf9e,0x94aaa1,0x416f72,0xab9c99,0x536f66,0x26474b,0xd2b179},
  {0x528eaf,0xe3dec1,0xe6e4ca,0xffeaba,0x7faeaa,0x286f7d,0x90aaa2,0x416957,0x193f40,0xc9c995},
  {0x6d6b9d,0xffa471,0xf5948a,0xffce85,0xa49a9e,0x425879,0xad858a,0x564d63,0x2b354e,0xe0a574},
  {0x17233e,0x617b8c,0x667696,0xf4e5ae,0x526e80,0x223f55,0x657584,0x344e54,0x152e3f,0x9da79a}
};
inline void palette(Color *p,Water family,int time,int place){
  const Light& l=lights[time];bool marine=place>=96;
  Color water=marine?0x3a9b9a:family==Marsh?0x879359:family==Wide||family==Bend?0xa18a55:0x439374;
  int strength=time==1?86:time==3?14:39;
  ramp(p,0,7,l.sky,l.horizon);
  for(int i=0;i<7;i++)p[50+i]=mix(p[i],p[i+1],128);
  ramp(p,8,11,mix(l.sky,l.clouds,105),mix(l.clouds,l.horizon,60));
  p[Sun]=l.sun;p[Glow]=mix(l.horizon,l.sun,112);
  ramp(p,14,21,mix(l.water,water,strength),mix(l.nearWater,water,strength/2));
  ramp(p,22,25,mix(p[17],l.horizon,52),mix(l.horizon,l.sun,103));
  p[Far]=mix(l.fog,l.horizon,95);p[Mist]=mix(l.fog,l.canopy,36);p[Ridge]=mix(l.fog,l.canopy,110);
  p[Wood]=mix(l.canopy,l.shade,135);p[Crown]=l.canopy;p[Leaf]=mix(l.canopy,l.highlight,62);
  p[SunLeaf]=mix(l.canopy,l.highlight,130);p[Shadow]=l.shade;p[Reed]=mix(l.shade,l.canopy,140);
  p[Tip]=mix(l.canopy,l.highlight,160);p[Sand]=mix(l.highlight,l.fog,70);
  p[Stone]=mix(l.fog,l.shade,125);p[StoneLight]=mix(l.fog,l.highlight,88);p[Deep]=mix(p[20],l.shade,100);
  p[Post]=mix(l.shade,0x342d30,95);p[Timber]=mix(l.canopy,0xad7555,time==3?48:145);
  p[Roof]=mix(l.canopy,0xc77e61,time==3?56:170);p[Wall]=mix(l.highlight,0xf4ca91,90);
  p[Window]=mix(l.shade,0x374651,120);p[Gold]=time==3?0xffc574:0xf6c779;
  p[Canvas]=mix(l.horizon,0xe9dcaf,75);p[Petal]=mix(l.clouds,0xffadab,150);
  p[Wake]=mix(p[18],l.horizon,105);p[Star]=mix(l.horizon,0xffeed3,130);
  // Adjacent-value pigments for arrival textures use the same local light.
  p[57]=mix(p[Sand],p[Timber],97);p[58]=mix(p[Reed],p[Leaf],94);
  p[59]=mix(p[Stone],p[StoneLight],63);p[60]=mix(p[Timber],p[Post],73);
  p[61]=mix(p[Wood],p[Timber],85);p[62]=mix(p[Post],p[Stone],64);
  p[63]=mix(p[Crown],p[Leaf],134);
}
// Column-major, bottom-to-top storage also permits in-place LCD expansion.
struct Image {
  uint8_t *data;
  int offset(int x,int y) const{return x*height+height-1-y;}
  void dot(int x,int y,int c){if(unsigned(x)<width && unsigned(y)<height)data[offset(x,y)]=c;}
  uint8_t at(int x,int y)const{return data[offset(clamp(x,0,width-1),clamp(y,0,height-1))];}
  void span(int x,int y,int n,int c){
    if(unsigned(y)>=height)return;
    const int stop=minOf(width,x+n);
    for(x=maxOf(0,x);x<stop;++x)data[offset(x,y)]=c;
  }
  void rect(int x,int y,int w,int h,int c){
    for(int i=maxOf(0,y);i<minOf(y+h,height);i++)span(x,i,w,c);
  }
  void oval(int x,int y,int rx,int ry,int c){
    for(int row=-ry;row<=ry;row++){
      int half=rx;while(half>0 && half*half*ry*ry+row*row*rx*rx>rx*rx*ry*ry)--half;
      span(x-half,y+row,2*half+1,c);
    }
  }
  void line(int x,int y,int u,int v,int c){
    int dx=x<u?u-x:x-u,dy=y<v?y-v:v-y,sx=x<u?1:-1,sy=y<v?1:-1,err=dx+dy;
    for(;;){dot(x,y,c);if(x==u&&y==v)break;int e=2*err;if(e>=dy){err+=dy;x+=sx;}if(e<=dx){err+=dx;y+=sy;}}
  }
};
inline int noise(unsigned seed,int x,int spacing){
  int i=x/spacing,f=(x%spacing)*256/spacing;
  f=f*f*(768-2*f)/65536;
  int a=hash(seed+unsigned(i))%256,b=hash(seed+unsigned(i+1))%256;
  return (a*(256-f)+b*f)>>8;
}
inline void hut(Image& im,int x,int y,int w){
  im.rect(x-w,y-7,2*w,7,Wall);im.rect(x-2,y-5,4,5,Window);
  for(int k=0;k<5;k++)im.span(x-w-2+k,y-7-k,2*w+4-2*k,k==4?Timber:Roof);
  im.rect(x-w+1,y,1,3,Post);im.rect(x+w-2,y,1,3,Post);im.span(x-w-3,y+2,2*w+6,Timber);
}
inline void twig(Image& im,int x,int y,int h,int tint){
  im.line(x,y,x-1,y-h,Reed);im.line(x,y-2,x+3,y-h+2,tint);
  im.line(x,y,x-4,y-h/2,Reed);im.dot(x-1,y-h-1,tint);
}
inline void motif(Image& im,Feature f,int x,int y,Random& r){
  int w=r.between(8,15);
  switch(f){
    case Kitchen:case Boathouse:case Market:
      hut(im,x,y,w);im.span(x-w-4,y+3,w*2+9,Post);
      if(f==Market||f==Kitchen)hut(im,x+w+8,y-1,6);
      break;
    case Rail:case Bridge:{
      int left=x<width/2?0:x-16,right=x<width/2?x+16:width-1,deck=y-6;
      im.span(left,deck,right-left,Post);im.span(left,deck-1,right-left,StoneLight);
      for(int i=left+3;i<right;i+=12){im.rect(i,deck+1,2,8,Stone);im.line(i,deck-2,i+5,deck-5,Post);im.line(i+5,deck-5,i+11,deck-2,Post);}
      if(f==Rail){im.rect(x-9,deck-6,18,4,Roof);for(int i=0;i<4;i++)im.rect(x-7+i*4,deck-5,2,1,Canvas);}
      break;
    }
    case Pier:case Lantern:case Marker:case Nets:
      im.span(x-w,y,w*2,Timber);im.rect(x-w+2,y+1,2,6,Post);im.rect(x+w-3,y+1,2,5,Post);
      im.rect(x,y-12,1,13,Post);
      if(f==Nets){im.line(x,y-10,x+w,y-4,Canvas);for(int i=2;i<w;i+=3)im.line(x+i,y-9+i/2,x+i-2,y+i/3,Stone);}
      else if(f==Lantern){im.span(x,y-11,6,Post);im.rect(x+4,y-9,3,3,Gold);}
      else if(f==Marker){im.span(x+1,y-11,5,Roof);im.span(x+1,y-10,3,Roof);}
      break;
    case Heron:
      im.line(x-2,y,x-2,y-5,Post);im.line(x+1,y,x,y-5,Post);im.oval(x,y-6,4,2,Canvas);
      im.line(x+2,y-7,x+4,y-12,Canvas);im.span(x+3,y-12,5,Gold);break;
    case Lotus:case Reeds:case Roots:case Snag:
      for(int i=0;i<7;i++){int u=x+r.between(-w,w),v=y+r.between(0,4);
        if(f==Lotus){im.oval(u,v,3,1,Leaf);im.span(u-1,v-2,3,Petal);}
        else if(f==Snag||f==Roots){im.line(u,v,u-4,v-6,Post);im.line(u-2,v-3,u+2,v-7,Timber);}
        else twig(im,u,v,r.between(4,12),Tip);}
      break;
    case Rocks:case Ford:
      for(int i=0;i<6;i++){int u=x+r.between(-w,w),v=y+r.between(-2,3);im.oval(u,v,r.between(2,5),2,Stone);im.span(u-2,v-1,4,StoneLight);}break;
    case Raft:case Ferry:case Boat:case Lamps:case Sail:case Basket:case Paper:break;
    case Buoy:im.oval(x,y,3,2,Roof);im.rect(x-1,y-5,2,5,Canvas);im.dot(x,y-6,Gold);break;
  }
}
struct Layout {unsigned seed; int place,period,horizon,sunX; Recipe recipe;};
inline void pingUrbanBanks(Image& im,int horizon,int period,int motifX,int motifY){
  auto dry=[&](int x,int y,int ink){
    if(unsigned(x)>=width||unsigned(y)>=height)return;
    const int from=im.at(x,y);
    if(!((from>=WaterTop&&from<Far)||from==Deep||from==Wake))im.dot(x,y,ink);
  };
  // Reuse real dry inks from the existing initialized LCD palette.
  for(int y=motifY-12;y<=motifY+3;y++)
    for(int x=motifX-20;x<motifX+31;x++){
      const int c=im.at(x,y);
      if(c==Roof||c==Wall||c==Window||c==Timber||c==Post)
        dry(x,y,y<horizon?Crown:y==horizon?Wood:y<=horizon+2?Stone:Wood);
    }
  for(int side=0;side<2;side++){
    const int extent=side?81:111;
    for(int e=0;e<extent;e++){
      const int x=side?width-1-e:e;
      const int t=extent-e,lip=horizon-1+t*t/(extent*(side?16:12));
      for(int y=lip-3-t/22;y<=lip;y++){
        const bool cap=(y==lip-2&&((e+side*3)/11)%4<2);
        dry(x,y,cap?StoneLight:((x+y/2)%12<2?Stone:Wood));
      }
    }
  }
  for(int y=horizon-29;y<horizon-12;y++)
    for(int x=11;x<31;x++)dry(x,y,y<horizon-27?Stone:Wall);
  for(int x=13;x<29;x+=5)for(int y=horizon-23;y<horizon-14;y+=5)
    dry(x,y,period>=2&&x%3==0?Gold:Window);
  for(int x=190;x<224;x++){
    const int y=horizon-20-(x<201?(x-190)/3:x<216?4:(224-x)/4);
    for(int z=y;z<=horizon-13;z++)dry(x,z,z<y+2?Roof:StoneLight);
  }
  constexpr int trees[][5]={{0,1,21,19,8},{19,0,14,15,11},{37,-1,15,12,10},
    {54,-3,13,9,7},{69,-4,11,8,5},{84,-5,9,6,4},{97,-5,6,4,3},
    {164,-5,8,6,4},{175,-3,11,8,6},{190,-1,13,11,7},{207,1,17,14,10},
    {224,4,19,16,9},{240,5,21,18,8}};
  for(int j=0;j<13;j++){
    const auto& tree=trees[j];
    for(int dy=-tree[3];dy<tree[3]/2;dy++){
      for(int dx=-tree[2];dx<=tree[2];dx++){
        const int y=horizon+tree[1]+dy,x=tree[0]+dx;
        const int curve=dx*dx*100/(tree[2]*tree[2])+dy*dy*95/(tree[3]*tree[3]);
        const unsigned speck=hash(unsigned(x*149+y*71+j*11));
        if(curve<85+int(speck%30))
          dry(x,y,curve<58&&dy<-tree[4]/2?(speck%5==0?SunLeaf:Leaf):curve<79?Crown:Wood);
      }
    }
  }
  for(int y=122;y<height;y++) for(int x=0;x<width;x++){
    const int e=minOf(x,width-1-x);
    if(e>=(x<width/2?27:15)||im.at(x,y)!=Shadow)continue;
    if(((x+((y/4)&1)*3)%11)<3)dry(x,y,Wood);
  }
}
inline void render(Image im,Color *colors,int place,int time,Layout* layout=nullptr){
  constexpr int count=sizeof(recipes)/sizeof(recipes[0]);
  place=clamp(place,0,count-1);time=clamp(time,0,3);
  Recipe composition=recipes[place];Water water=composition.water;bool sea=place>=96;
  unsigned seed=hash(0xbba66aU+unsigned(place)*0x23963U);
  Random r{seed};palette(colors,water,time,place);
  int horizon=r.between(56,77),sunX=r.between(19,221);
  if(layout)*layout={seed,place,time,horizon,sunX,composition};
  int sunY=time==1?r.between(10,23):time==3?r.between(9,32):r.between(horizon-32,horizon-14);
  // Interleave neighboring sky values at the pixel scale to soften band edges.
  for(int y=0;y<horizon;y++)for(int x=0;x<width;x++){
    int value=14*y*16/horizon,band=clamp((value+int(hash(seed+unsigned(y*width+x))&15))>>4,0,14);
    im.dot(x,y,band%2?50+band/2:band/2);
  }
  // Sky decorations have an independent stream so landmarks stay put at night.
  Random sky{seed+1593};
  if(time==3){for(int i=0;i<53;i++){int x=sky.between(1,238),y=sky.between(2,horizon-12);im.dot(x,y,Star);}}
  im.oval(sunX,sunY,time==3?5:8,time==3?5:8,time==3?Sun:Glow);
  if(time!=3)im.oval(sunX,sunY,6,6,Sun);
  for(int i=0,n=r.between(5,9);i<n;i++){
    int x=r.between(-20,223),y=r.between(7,horizon-17),len=r.between(10,49);
    for(int k=0;k<len;k+=3){
      int rise=1+minOf(k,len-k)/9;
      int offset=r.between(-2,1),rx=r.between(4,10),ry=r.between(1,rise+1);
      im.oval(x+k,y+offset,rx,ry,Cloud+i%3);
      if(k%2==0)im.span(x+k,y+1,r.between(4,14),Cloud+3);
    }
  }
  bool islands=water==Gulf||water==Island||water==Karst||water==Headland;
  int openSide=r.between(0,1),vanish=r.between(47,193);
  for(int layer=0;layer<3;layer++){
    unsigned layerSeed=hash(seed+unsigned(layer)*223U);
    int spacing=r.between(17,50)+layer*4,peak=r.between(8,17);
    if(water==Karst||water==Gorge||water==Foothill)peak+=14;
    if(water==Marsh||water==Estuary||water==Gulf)peak=layer?7:11;
    if(water==Karst)spacing=maxOf(10,spacing-12);
    for(int x=0;x<width;x++){
      int n=noise(layerSeed,x,spacing),detail=noise(layerSeed+5,x,7);
      int elevation=(n*peak)/255+(detail*peak)/1400+(2-layer)*3;
      if(islands){
        int cutoff=water==Gulf?164:water==Karst?90:105;
        if(water==Karst)elevation=clamp((n-cutoff)*3,0,205)*peak/180+detail/72;
        else elevation=maxOf(0,n-cutoff)*peak/(255-cutoff);
        if(n<cutoff)elevation=0;
      }else if(water==Gorge||water==Bend||water==Stream){
        int distance=x>vanish?x-vanish:vanish-x;
        elevation+=distance*(water==Gorge?20:9)/135;
        elevation=elevation*(75+minOf(96,distance))/160;
      }
      if(water==Headland)elevation=elevation*(openSide?x:width-x)/width;
      int ridgeY=horizon-elevation;
      for(int y=ridgeY;y<horizon;y++)im.dot(x,y,Far+layer);
      if(elevation>9){
        int ledge=noise(layerSeed+263,x,6)*elevation/376;
        for(int d=2;d<ledge;d++){
          if(noise(layerSeed+135,unsigned(x+d/2),8)+d*4>185)im.dot(x,ridgeY+d,layer==2?Mist:Far);
        }
      }
      if(layer==2&&elevation>6 && (hash(seed+x)%7)<3)im.dot(x,ridgeY+1,water==Karst?StoneLight:Mist);
    }
  }
  int groveLength=r.between(18,99);
  for(int i=0;i<46;i++){
    int x=r.between(0,width-1),distance=x>vanish?x-vanish:vanish-x;
    if(islands&&(im.at(x,horizon-4)<Far||im.at(x,horizon-4)>=50))continue;
    if(!islands&&(distance<20||((openSide?x:width-x)>groveLength&&i%4)))continue;
    int size=r.between(2,6);
    im.oval(x,horizon-1,size+1,size,Crown);im.oval(x+2,horizon-3,size-1,maxOf(1,size-2),Leaf);
  }
  for(int y=horizon;y<height;y++){
    int depth=y-horizon;
    im.span(0,y,width,WaterTop+minOf(7,depth*8/(height-horizon)));
    int dx=int(hash(seed+unsigned(y))%7)-3;
    for(int x=0;x<width;x++){
      int src=im.at(x+dx,horizon-1-depth*3/2);
      unsigned n=hash(seed+unsigned(x/4)+unsigned(y)*263)%16;
      if(depth<20 && src>=Far && src<50 && n>depth/2)im.dot(x,y,depth<4?Ridge:Deep);
    }
    int mid=sunX+r.between(-3,3),splay=3+depth/5;
    for(int k=0;k<2;k++){
      int x=mid+r.between(-splay,splay);
      im.span(x,y,r.between(1,3+depth/9),WaterLight+minOf(3,(depth+k)%4));
    }
  }
  for(int i=0;i<465;i++){
    int x=r.between(-8,239),y=r.between(horizon+1,height-1),depth=y-horizon;
    int length=r.between(1,3+depth/8),base=WaterTop+minOf(7,depth*8/(height-horizon));
    im.span(x,y,length,i%6==0?WaterLight:clamp(base+(i%2?1:-1),WaterTop,WaterTop+7));
  }
  // A tapering arm of land gives narrow waters a bend before the far shore.
  if(water==Bend||water==Gorge||water==Stream||water==Marsh||water==Estuary){
    int extent=r.between(54,149),base=horizon+r.between(12,22);
    bool fromLeft=vanish>100;
    for(int i=0;i<extent;i++){
      int x=fromLeft?i:width-1-i,remain=extent-i;
      int edge=horizon+2+(base-horizon)*remain*remain/(extent*extent);
      int high=2+remain*7/extent+noise(seed+114,i,11)/66;
      for(int y=edge-high;y<=edge;y++)im.dot(x,y,y<edge-high/2?Crown:Wood);
      im.dot(x,edge,Sand);if(i%6<3)im.dot(x,edge+1,Deep);
      if(i%3==0 && remain>15)twig(im,x,edge-high+2,r.between(2,6),Leaf);
    }
  }
  int bank=water==Stream||water==Bend||water==Gorge?r.between(52,99):sea?r.between(18,55):r.between(27,79);
  int baseY=r.between(114,142),leftBank=r.between(0,1);
  for(int side=0;side<2;side++){
    int length=side?bank/3:bank;
    bool left=side?!leftBank:leftBank;
    for(int i=0;i<length;i++){
      int remain=length-i,x=left?i:width-1-i;
      int y=height-remain*remain*(height-baseY)/(length*length)+(int(noise(seed+18,i,12))-128)/27;
      for(int j=y;j<height;j++){
        unsigned fleck=hash(unsigned(x/3 + (j/2)*457)+seed);
        im.dot(x,j,sea?(fleck%9==0?StoneLight:Stone):(fleck%8==0?Wood:Shadow));
      }
      im.dot(x,y,sea?StoneLight:Leaf);
      if(i%3==0 && !sea)twig(im,x,y,r.between(3,10),Reed);
      if(i%9==0 && sea){im.oval(x,y,5+(i%3),3,Stone);im.span(x-2,y-2,4,StoneLight);}
    }
  }
  // Near banks carry illustrated foliage, weathered pilings or coastal rock.
  Random detail{seed+0x4b739};
  int framing=detail.between(0,5);
  int edge=leftBank?0:width-1,sign=leftBank?1:-1;
  if(!sea && (water==Stream||framing<=1)){
    int reach=detail.between(21,52),y=detail.between(13,28);
    im.line(edge,y+11,edge+sign*reach,y-6,Wood);
    for(int i=0;i<19;i++){
      int dx=detail.between(0,reach),dy=y+9-dx*14/reach+detail.between(-8,5);
      int rx=detail.between(3,9),ry=detail.between(2,5),x=edge+dx*sign;
      im.line(x,dy,x+sign*5,dy-5,Wood);im.oval(x,dy,rx,ry,Wood);
      im.oval(x+1,dy-2,maxOf(2,rx-2),maxOf(1,ry-2),Crown);im.span(x-2,dy-ry,3,Leaf);
    }
  }else if(framing<=3 && (sea||water==Lake)){
    int x=edge+sign*detail.between(7,19),y=detail.between(116,136);
    im.rect(x-2,y,5,height-y,Post);im.rect(x-1,y,2,height-y,Timber);
    im.oval(x,y,3,1,StoneLight);im.span(x-3,y+4,7,Canvas);im.span(x-3,y+6,7,Canvas);
    im.line(x,y+6,edge,y+15,Timber);
  }else if(!sea){
    for(int i=0;i<8;i++){
      int x=edge+sign*detail.between(0,26),y=detail.between(145,158);
      int h=detail.between(8,24);
      im.line(x,y,x+sign*3,y-h,Reed);im.line(x,y-1,x+sign*9,y-h+3,Leaf);
      im.span(x+sign*3-1,y-h-2,2,Tip);
    }
  }
  int featureX=openSide?r.between(23,102):r.between(141,213),featureY=horizon+r.between(2,11);
  if(composition.feature==Heron||composition.feature==Lotus||composition.feature==Rocks||
      composition.feature==Snag||composition.feature==Roots)featureY+=r.between(8,19);
  motif(im,composition.feature,featureX,featureY,r);
  if(water==Marsh){for(int i=0;i<35;i++){
    int x=leftBank?r.between(-4,52):r.between(189,243),y=r.between(100,153);
    im.oval(x,y,2+y/65,1,Reed);if(i%7==0)im.span(x-1,y-2,3,Petal);
  }}
  if(place==52)pingUrbanBanks(im,horizon,time,featureX,featureY);
}
}
