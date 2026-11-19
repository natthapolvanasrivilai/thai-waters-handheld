#pragma once
#include <Arduino.h>
constexpr uint32_t releaseNumber=7;
constexpr uint32_t productModel=0x52454645; // Riffle Rev E / 3.5B 31137
bool releaseKeyValid(const String& hex);
void fetchRelease(String url,String key);
bool updateBusy();

