#include "Board.h"
#include <Wire.h>
#include <SensorQMI8658.hpp>
#define XPOWERS_CHIP_AXP2101
#include <XPowersLib.h>
namespace {
Arduino_ESP32QSPI bus(12,5,1,2,3,4);
Arduino_AXS15231B panel(&bus,-1,0,false,320,480);
SensorQMI8658 imu;
XPowersPMU pmu;
bool readBytes(uint8_t addr,const uint8_t* cmd,size_t len,uint8_t* out,size_t count,bool stop){
  Wire.beginTransmission(addr);Wire.write(cmd,len);
  if(Wire.endTransmission(stop)!=0 || Wire.requestFrom(addr,count)!=count)return false;
  return Wire.readBytes(out,count)==count;
}
bool writeReg(uint8_t addr,uint8_t reg,uint8_t val){
  Wire.beginTransmission(addr);Wire.write(reg);Wire.write(val);return Wire.endTransmission()==0;
}
bool resetPanel(){
  // TCA9554 P1 only. Preserve the other expander outputs.
  uint8_t cfg=3,out=1,cv=0,ov=0;
  if(!readBytes(0x20,&cfg,1,&cv,1,false)||!readBytes(0x20,&out,1,&ov,1,false))return false;
  if(!writeReg(0x20,1,ov|2)||!writeReg(0x20,3,cv&~2))return false;
  delay(10);if(!writeReg(0x20,1,ov&~2))return false;
  delay(10);if(!writeReg(0x20,1,ov|2))return false;
  delay(200);return true;
}
}
Arduino_Canvas screen(320,480,&panel,0,0,1);
bool screenOK=false,imuOK=false,powerOK=false;
void beginBoard(){
  Wire.begin(8,7,400000);Wire.setTimeOut(20);
  if(pmu.begin(Wire,AXP2101_SLAVE_ADDRESS,8,7)){
    powerOK=pmu.setChargeTargetVoltage(XPOWERS_AXP2101_CHG_VOL_4V2)
      && pmu.setChargerConstantCurr(XPOWERS_AXP2101_CHG_CUR_300MA)
      && pmu.getChargeTargetVoltage()==XPOWERS_AXP2101_CHG_VOL_4V2
      && pmu.getChargerConstantCurr()==XPOWERS_AXP2101_CHG_CUR_300MA;
  }
  screenOK=resetPanel() && screen.begin();
  if(screenOK){pinMode(6,OUTPUT);analogWrite(6,145);screen.setTextWrap(false);}
  imuOK=imu.begin(Wire,QMI8658_L_SLAVE_ADDRESS,8,7) || imu.begin(Wire,QMI8658_H_SLAVE_ADDRESS,8,7);
  if(imuOK){
    imu.configAccelerometer(SensorQMI8658::ACC_RANGE_4G,SensorQMI8658::ACC_ODR_125Hz,SensorQMI8658::LPF_MODE_2);
    imu.enableAccelerometer();
  }
}
bool acceleration(creek::Vec& g){return imuOK && imu.getAccelerometer(g.x,g.y,g.z);}
Field readWheel(int& raw){
  uint8_t reg=0x0b,b[3];
  if(!readBytes(0x36,&reg,1,b,3,false))return Field::Missing;
  if(b[0]&0x08)return Field::Strong;
  if(b[0]&0x10)return Field::Weak;
  if(!(b[0]&0x20))return Field::NoMagnet;
  raw=((b[1]&15)<<8)|b[2];return Field::Good;
}
bool touchPoint(int& x,int& y){
  const uint8_t cmd[]={0xb5,0xab,0xa5,0x5a,0,0,0,0x0e,0,0,0};
  uint8_t b[14]{};
  if(!readBytes(0x3b,cmd,sizeof(cmd),b,sizeof(b),true)||b[0]==0xff||b[1]!=1)return false;
  const int px=((b[2]&15)<<8)|b[3],py=((b[4]&15)<<8)|b[5];
  if(px>=320||py>=480)return false;
  x=py;y=319-px;return true;
}
#include "HardwareAPI.h"
namespace hardware {
SensorQMI8658& motion(){return imu;}
XPowersPMU& power(){return pmu;}
TwoWire& bus(){return Wire;}
bool gyroPower(bool enabled){
 if(!imuOK)return false;
 if(!enabled)return imu.disableGyroscope();
 imu.configGyroscope(SensorQMI8658::GYR_RANGE_256DPS,SensorQMI8658::GYR_ODR_112_1Hz,SensorQMI8658::LPF_MODE_2);
 return imu.enableGyroscope();
}
Sample sample(){
 Sample s{};s.uptimeMs=millis();s.reel=-1;
 s.accelRawOK=imuOK&&imu.getAccelRaw(s.accelRaw);s.gyroRawOK=imuOK&&imu.getGyroRaw(s.gyroRaw);
 if(s.accelRawOK){float k=imu.getAccelerometerScales();s.accelG={s.accelRaw[0]*k,s.accelRaw[1]*k,s.accelRaw[2]*k};s.accelOK=true;}
 if(s.gyroRawOK){float k=imu.getGyroscopeScales();s.gyroDps={s.gyroRaw[0]*k,s.gyroRaw[1]*k,s.gyroRaw[2]*k};s.gyroOK=true;}
 s.field=readWheel(s.reel);return s;
}
}
