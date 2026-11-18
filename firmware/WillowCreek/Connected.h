#pragma once
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


void eventTick(int spot);void toggleEvent();void eventCatch();const char* eventStatus();bool eventActive();
