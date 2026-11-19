#pragma once
#include <stdint.h>
uint32_t pondUtc();
void printCatchRecord(uint32_t index);
void beginConnected();
void tickConnected();
void startPairing();
void stopPairing();
void toggleRadio();
bool radioEnabled();
const char* networkStatus();
const char* setupName();
const char* setupCode();
const char* pondClock();
int pondPeriod();
void checkUpdate();
const char* updateStatus();
void confirmUpdateHealth(bool healthy);


void eventTick(int spot);void toggleEvent();void eventCatch(int spot,int species,int cm,unsigned landedDay);unsigned eventDay();const char* cupGoal();
const char* cupBait();const char* cupStanding();const char* eventStatus();bool eventActive();
