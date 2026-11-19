# Browser verification
Run npm ci and npm test from this directory. Set BROWSER_PATH to the local Chromium or Edge executable on other systems. The tests open the private offline artifact, exercise normal screen and crank controls, and validate the phone calibration using injected motion samples. The device test uses Chromium's software WebGL backend so it can run headlessly.

The tournament test starts an isolated Node 22.13+ LAN host with an in-memory SQLite database. It pairs two independent phone browser profiles, files held catches and verifies both rankings on the LCD. Install the dependencies in game/lan as well as this directory before running the suite.

The bait test follows Rod workshop, travel, journal, cast and hook controls. It checks an empty presentation without a bite or reward, then reloads a saved bottom-shrimp setup and hooks a prawn at dusk. The native bait and panel fixtures cover the same engine restrictions and handheld Preferences persistence.

### First-person arrival pixels

Run `node arrival.cjs` to check navigation, reduced motion, transparent palette pixels and exact 2 × 2 LCD scaling. For the full pixel comparison, compile `firmware/tests/arrival_pixels.cpp` using C++17 with `-O2 -ffp-contract=off` from the repository root. Redirect its output to a UTF-8 text file and pass that path to `node verification/browser-tests/arrival-pixels.cjs`. The comparison covers four times in each of 117 destinations.
