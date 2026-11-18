#include "Sound.h"
#include "Synth.h"
#include <Arduino.h>
#include <ESP_I2S.h>
#include <Wire.h>
#include <cmath>
#include "es8311.h"

namespace {
constexpr int sampleRate=16000;
I2SClass output;
portMUX_TYPE lock=portMUX_INITIALIZER_UNLOCKED;
SoundSettings current;
bool fight=false;
uint32_t signalNumber=0;
CreekSynth synth;
void stream(void*) {
  int16_t buffer[256];
  uint32_t seen=0;
  for(;;){
    portENTER_CRITICAL(&lock);
    SoundSettings s=current;bool chase=fight;uint32_t signal=signalNumber;
    portEXIT_CRITICAL(&lock);
    synth.render(buffer,128,s,chase,signal!=seen);
    seen=signal;
    output.write(reinterpret_cast<uint8_t*>(buffer),sizeof(buffer));
  }
}
}
bool startSound(){
  synth.begin();
  output.setPins(13,15,16,-1,44);
  if(!output.begin(I2S_MODE_STD,sampleRate,I2S_DATA_BIT_WIDTH_16BIT,I2S_SLOT_MODE_STEREO))return false;
  es8311_handle_t c=es8311_create(I2C_NUM_0,ES8311_ADDRRES_0);
  es8311_clock_config_t clk{false,false,true,256*sampleRate,sampleRate};
  if(!c || es8311_init(c,&clk,ES8311_RESOLUTION_16,ES8311_RESOLUTION_16)!=ESP_OK ||
     es8311_voice_volume_set(c,65,nullptr)!=ESP_OK || es8311_voice_mute(c,false)!=ESP_OK)return false;
  return xTaskCreatePinnedToCore(stream,"creek-audio",4096,nullptr,2,nullptr,0)==pdPASS;
}
void setSound(const SoundSettings& s,bool chase,bool bite){
  portENTER_CRITICAL(&lock);
  current=s;fight=chase;if(bite && s.cue!=1)signalNumber++;
  portEXIT_CRITICAL(&lock);
}
