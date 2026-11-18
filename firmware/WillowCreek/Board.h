#pragma once
#include "Creek.h"
#include <Arduino_GFX_Library.h>
extern Arduino_Canvas screen;
extern bool screenOK,imuOK,powerOK;
enum class Field { Missing, Weak, Strong, NoMagnet, Good };
void beginBoard();
bool acceleration(creek::Vec& gravity);
Field readWheel(int& raw);
bool touchPoint(int& x,int& y);
