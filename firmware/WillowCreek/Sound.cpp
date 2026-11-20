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
bool fight=false,held=false,running=false,missed=false;
uint32_t signalNumber=0;
int pendingClick=0;
uint8_t pendingFoley=0;
creek::LandingCue pendingLanding;
CreekSynth synth;
void stream(void*) {
  int16_t buffer[256];
  uint32_t seen=0;
  for(;;){
    portENTER_CRITICAL(&lock);
    SoundSettings s=current;bool chase=fight,landed=held,surge=running,lost=missed;uint32_t signal=signalNumber;
    int click=pendingClick;pendingClick=0;
    const auto foley=pendingFoley;pendingFoley=0;
    auto landing=pendingLanding;pendingLanding={};
    portEXIT_CRITICAL(&lock);
    synth.render(buffer,128,s,chase,signal!=seen,click,landing,foley,landed,surge,lost);
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
void setSound(const SoundSettings& s,bool chase,bool bite,int reelClick,creek::LandingCue landing,uint8_t fishingSounds,bool landed,bool surge,bool lost){
  portENTER_CRITICAL(&lock);
  pendingFoley|=fishingSounds;current=s;fight=chase;held=landed;running=surge;missed=lost;if(bite && s.cue!=1)signalNumber++;
  if(!held || s.cue==1 || !s.cueVolume)pendingLanding={};
  else if(landing.active())pendingLanding=landing;
  if(bite || !s.reelVolume)pendingClick=0;else if(reelClick)pendingClick=reelClick;
  portEXIT_CRITICAL(&lock);
}
