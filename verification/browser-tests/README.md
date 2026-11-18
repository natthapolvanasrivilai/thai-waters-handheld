# Browser verification
Run npm ci and npm test from this directory. Set BROWSER_PATH to the local Chromium or Edge executable on other systems. The tests open the private offline artifact, exercise normal screen and crank controls, and validate the phone calibration using injected motion samples. The device test uses Chromium's software WebGL backend so it can run headlessly.
