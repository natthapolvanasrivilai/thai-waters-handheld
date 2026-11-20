#pragma once
#include "Landscape.h"

namespace arrival {
constexpr unsigned duration=4200, raiseRod=3330;
enum Route { Footpath, Hike, Drive, Longtail };
inline Route landing(int site,int pool){
  const auto r=scenery::recipes[site];
  if(site==16)return Footpath; // Kwan Phayao waterfront promenade
  if(pool==4 || r.water==scenery::Karst || r.feature==scenery::Ferry || r.feature==scenery::Raft)return Longtail;
  if(r.water==scenery::Gorge || r.water==scenery::Foothill || r.water==scenery::Stream)return Hike;
  if(r.feature==scenery::Bridge || r.feature==scenery::Market || r.feature==scenery::Rail || r.feature==scenery::Lamps)return Drive;
  return Footpath;
}
inline const char* description(Route route){
  const char* names[]={"Walking down to the bank","Hiking the shore trail","Driving to the landing","Taking the longtail boat"};
  return names[route];
}
inline float ease(unsigned ms,unsigned start,unsigned length){
  if(ms<=start)return 0;
  if(ms>=start+length)return 1;
  const float t=float(ms-start)/length;
  return t*t*(3-2*t);
}
// Metres per second at cruise. Timings share the existing rod-raise cue.
constexpr unsigned rampEnd=300, cruiseEnd=2680, revealStart=3030, revealEnd=3760;
struct Motion {float distance, speedFraction;};
inline Motion motion(Route route,unsigned ms){
  constexpr float speeds[]={1.20f,.95f,6.f,3.f};
  constexpr unsigned braking=raiseRod-cruiseEnd;
  constexpr float beforeBraking=rampEnd*.5f+(cruiseEnd-rampEnd);
  const float cruise=speeds[route]*.001f;
  // The integral of smoothstep is t^3 * (1 - t/2).
  auto integrated=[](float t){return t*t*t*(1.f-.5f*t);};
  if(ms<rampEnd){
    const float t=float(ms)/rampEnd;
    return {cruise*rampEnd*integrated(t),ease(ms,0,rampEnd)};
  }
  if(ms<cruiseEnd)return {cruise*(rampEnd*.5f+ms-rampEnd),1.f};
  if(ms>=raiseRod)return {cruise*(beforeBraking+braking*.5f),0.f};
  const float t=float(ms-cruiseEnd)/braking;
  return {cruise*(beforeBraking+braking*(t-integrated(t))),1.f-ease(ms,cruiseEnd,braking)};
}
// Smooth periodic camera displacement without requiring trig in the LCD/WASM renderer.
inline float cycle(float phase){
  float t=(phase-unsigned(phase))*2.f;
  if(t>1.f)t=2.f-t;
  return 1.f-2.f*t*t*(3.f-2.f*t);
}
enum Kind {Line,Triangle,Sprite};
enum Surface {Grass=64, Earth, Gravel, Asphalt, Gunwale, Dashboard};
enum Detail { Broadleaf, Rushes };
struct Shape {int16_t kind,ink,x,y,u,v,a,b;};
struct Point {float x,y;};
constexpr int maxShapes=384;
struct Frame {
  Shape shapes[maxShapes];int count;
  float distance,eye,horizon,center,bend,boatShift,boatDrop;
  unsigned seed;
  unsigned reveal;
  void sprite(Point a,Point b,int detail){
    if(count<maxShapes)shapes[count++]={Sprite,int16_t(detail),int16_t(a.x),int16_t(a.y),int16_t(b.x),int16_t(b.y),0,0};
  }
  void line(Point p,Point q,int ink){
    if(count<maxShapes)shapes[count++]={Line,int16_t(ink),int16_t(p.x),int16_t(p.y),int16_t(q.x),int16_t(q.y),0,0};
  }
  void tri(Point p,Point q,Point r,int ink){
    if(count<maxShapes)shapes[count++]={Triangle,int16_t(ink),int16_t(p.x),int16_t(p.y),int16_t(q.x),int16_t(q.y),int16_t(r.x),int16_t(r.y)};
  }
  void quad(Point p,Point q,Point r,Point s,int ink){tri(p,q,r,ink);tri(p,r,s,ink);}
};
// A feature has a fixed position along the route. Advancing the eye makes it
// expand from the vanishing point, pass the shoulder and leave the frame.
struct Camera {
  float distance, eye, horizon, center, bend;
  Point at(float lateral,float height,float world)const{
    const float z=world-distance,scale=175.f/z;
    return {center+scale*(lateral+bend*z*z*.002f),horizon+(eye-height)*scale};
  }
};
// Broadleaf crown built from overlapping sunlit and shaded lobes.
inline void crown(Frame& f,const Camera& c,float x,float height,float z,float size){
  using namespace scenery;
  f.sprite(c.at(x-size,height+size,z),c.at(x+size,height-.43f*size,z),Broadleaf);
}
inline void ground(Frame& f,const Camera& c,Route route,int site){
  using namespace scenery;
  const bool road=route==Drive,trail=route==Hike;
  const float half=road?3.f:trail?1.05f:1.55f;
  const float end=22.f,near=c.distance+1.f;
  if(near>=end)return;
  // Draw far to near. Painted marks, stones and grass are in world coordinates.
  for(int row=21;row>=0;--row){
    const float far=float(row+1);
    if(far<=near)break;
    const float z=row<near?near:float(row);
    const auto seed=hash(unsigned(site*83+row));
    float left=-half-(trail?(row%3)*.16f:0),right=half;
    f.quad(c.at(-12,0,far),c.at(12,0,far),c.at(12,0,z),c.at(-12,0,z),Grass);
    f.quad(c.at(left,0,far),c.at(right,0,far),c.at(right,0,z),c.at(left,0,z),road?Asphalt:trail?Gravel:Earth);
    // Short grasses, leaf litter and gravel cover the margins at world scale.
    for(int j=0;j<2;j++){
      float side=(j?1.f:-1.f)*(half+.14f+(seed>>(4*j)&15)*.12f);
      float depth=far-.21f;
      if(depth<=near)continue;
      f.line(c.at(side,0,depth),c.at(side+.19f,.05f,depth),trail?Stone:Leaf);
      f.line(c.at(side-.12f,0,depth+.14f),c.at(side+.05f,.17f,depth+.14f),SunLeaf);
    }
    if(!road){
      float x=(int(seed%77)-38)*half/48.f;
      f.line(c.at(x,0,far),c.at(x+.075f,.012f,far-.04f),trail?StoneLight:Timber);
      if(row%3==0)f.line(c.at(-half+.22f,0,far),c.at(-half+.49f,0,z),trail?Stone:Wall);
    }
    if(road){
      f.line(c.at(-half+.14f,.01f,z),c.at(-half+.14f,.01f,far),Wall);
      f.line(c.at(half-.14f,.01f,z),c.at(half-.14f,.01f,far),Wall);
      if(row%3==0)f.quad(c.at(-.045f,.01f,far),c.at(.045f,.01f,far),c.at(.045f,.01f,z),c.at(-.045f,.01f,z),Canvas);
    }else if(row%2==0){
      float x=(int(seed%151)-75)*.011f;
      f.tri(c.at(x-.13f,0,far),c.at(x+.16f,0,far-.05f),c.at(x+.02f,.065f,far),trail?StoneLight:Timber);
      if(trail)f.line(c.at(left+.15f,0,far),c.at(right-.12f,.07f,far-.16f),Stone);
    }
    if(row%2==0){
      float side=(row%4?1.f:-1.f)*(half+.52f+(seed%7)*.12f);

      if(road){
        f.quad(c.at(side-.055f,0,far),c.at(side+.055f,0,far),c.at(side+.055f,.8f,far),c.at(side-.055f,.8f,far),Post);
        f.line(c.at(side,.58f,far),c.at(side,.78f,far),Canvas);
      }else{
        f.sprite(c.at(side-.45f,.65f,far),c.at(side+.43f,0,far),Rushes);
        if(row%4==0){
          float tree=side*1.72f;
          f.quad(c.at(tree-.09f,0,far),c.at(tree+.1f,0,far),c.at(tree+.08f,2.55f,far),c.at(tree-.06f,2.6f,far),Wood);
          f.line(c.at(tree,1.28f,far),c.at(tree-.49f,2.25f,far),Timber);
          crown(f,c,tree,2.55f,far,1.18f+(seed%5)*.18f);
        }
      }
    }
  }
}
inline void cockpit(Frame& f,float offset,float sink){
  using namespace scenery;
  auto p=[&](float x,float y)->Point{return {x+offset,y+sink};};
  // Driver's eye over the bonnet. The upper steering rim and near pillar pass
  // below the frame when the driver pulls in and looks up at the water.
  f.quad(p(-16,275),p(469,266),p(510,300),p(-16,307),Leaf);
  f.line(p(22,277),p(136,271),SunLeaf);f.line(p(354,271),p(453,269),SunLeaf);
  f.quad(p(-18,286),p(505,279),p(509,330),p(-18,330),Dashboard);
  f.quad(p(135,297),p(292,293),p(305,300),p(129,303),Wood);
  f.line(p(65,283),p(157,277),Stone);
  f.quad(p(-22,140),p(5,189),p(62,291),p(38,299),Wood);
  Point wheel[]={{261,331},{270,306},{289,292},{315,288},{338,297},{352,316},{356,331}};
  for(int i=0;i<6;i++)f.quad(p(wheel[i].x,wheel[i].y),p(wheel[i+1].x,wheel[i+1].y),
      p(wheel[i+1].x,wheel[i+1].y+7),p(wheel[i].x,wheel[i].y+7),StoneLight);
}
inline void prow(Frame& f,float drift,float sink){
  using namespace scenery;
  auto p=[&](float x,float y)->Point{return {x+drift,y+sink};};
  f.quad(p(122,326),p(236,208),p(244,208),p(352,326),Gunwale);
  f.tri(p(132,324),p(240,216),p(339,324),Gunwale);
  f.tri(p(121,324),p(237,209),p(159,324),Sand);
  f.line(p(147,319),p(237,214),Wall);
  f.line(p(327,320),p(244,215),Timber);
  f.tri(p(350,324),p(244,209),p(327,324),Roof);
  for(int i=0;i<4;i++){float y=239+i*20,w=(y-215)*.83f;f.quad(p(240-w,y),p(240+w,y),p(243+w,y+4),p(237-w,y+4),Timber);}
  f.quad(p(236,222),p(232,194),p(237,186),p(245,220),Post);
  f.quad(p(234,200),p(243,199),p(243,205),p(235,206),Gold);
  f.tri(p(243,202),p(259,210+drift*.5f),p(243,206),Petal);
}
inline void draw(Frame& f,int site,int pool,unsigned ms){
  f.count=0;
  f.reveal=unsigned(64.f*ease(ms,revealStart,revealEnd-revealStart));
  const Route route=landing(site,pool);
  const Motion travel=motion(route,ms);
  f.distance=travel.distance;
  if(ms>=revealEnd)return;
  const float settle=ease(ms,cruiseEnd,raiseRod-cruiseEnd);
  float side,vertical;
  if(route==Footpath||route==Hike){
    // Each step drives a rise/fall; alternating steps shift the eye side to side.
    const float strides=travel.distance/(route==Hike?.58f:.68f);
    side=2.f*cycle(strides*.5f+.25f);
    vertical=(route==Hike?3.f:1.5f)*cycle(strides+.25f);
  }else if(route==Drive){
    side=.85f*cycle(float(ms%690)/690.f+.25f);
    vertical=1.1f*cycle(float(ms%690)/690.f);
  }else{
    side=3.f*cycle(float(ms%1700)/1700.f+.25f);
    vertical=2.f*cycle(float(ms%1700)/1700.f);
  }
  side*=travel.speedFraction;vertical*=travel.speedFraction;
  Camera c{travel.distance,1.55f-.39f*settle,128.f+vertical,239.f+side,
           float(int(scenery::hash(site+5)%9)-4)*.7f};
  f.eye=c.eye;f.center=c.center;f.horizon=c.horizon;f.bend=c.bend;
  f.boatShift=route==Longtail?side:route==Drive?-side:0.f;
  f.boatDrop=route==Longtail?139*settle+vertical:route==Drive?116*settle:0.f;
  f.seed=scenery::hash(site);
  if(route==Longtail){
    // Passing surface flecks and mooring markers move relative to the bow.
    for(int i=0;i<39;i++){
      const unsigned h=scenery::hash(unsigned(site*57+i));
      float z=2.f+i*.69f;
      if(z<=c.distance+1.f)continue;
      float side=(i%2?1.f:-1.f)* (.8f+(h%73)*.08f);
      auto a=c.at(side,0,z),b=c.at(side+.16f+(h%4)*.09f,0,z);
      f.line(a,b,i%3==0?scenery::Wake:scenery::WaterLight);
    }
    const float markerZ=22.f;
    if(markerZ>c.distance+1){
      f.quad(c.at(-2.9f,0,markerZ),c.at(-2.82f,0,markerZ),c.at(-2.82f,1.44f,markerZ),c.at(-2.9f,1.44f,markerZ),scenery::Post);
      f.line(c.at(-2.86f,1.16f,markerZ),c.at(-2.86f,1.39f,markerZ),scenery::Canvas);
    }
    prow(f,f.boatShift,f.boatDrop);
  }else{
    ground(f,c,route,site);
    if(route==Drive)cockpit(f,f.boatShift,f.boatDrop);
  }
}
}
