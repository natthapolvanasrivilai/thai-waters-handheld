# Simulator source
The owner-private hosted build and phone QR are linked in [Phone playtest](sites/Phone-playtest.md). Phone touch screens start with the full fishing view. The 3D model initializes when the player selects Device view. The hosted `/event` service uses D1 for short-lived scores. Personal catches and tackle stay in each browser.

Open Thai-Waters-play.html directly for offline desktop play. For phone motion and shared events use lan/README.md. Toggle Screen only for an unobstructed gameplay view. On the modeled LCD, tap to cast or lift and tap MENU to navigate. Grab the right-side reel and move the pointer around its projected axle. Fold reel pivots the amber grip into the modeled well. The near-edge green shell, bezel, rotor, grip, collar and retainers come from the mechanical CAD. The Rev F model also includes the top power cap and optional rod grip. Surface finishes are a visualization.

Run python game/build.py from the repository root to regenerate the self-contained viewer from local assets. It has no CDN dependencies. To rebuild the renderer, enter game/src, run npm ci, then npx esbuild play-device.js --bundle --minify --format=iife --outfile=../assets/device-renderer.min.js. The WebAssembly is compiled from firmware/tests/bench.cpp with Zig C++ targeting wasm32-wasi and linked with wasm-ld --no-entry --export-dynamic --allow-undefined --strip-all. Use the functions imported by the packaged viewer. The firmware and browser share the game, pose, wheel and audio code.

Game data lives under content and locations.json. Stable IDs preserve existing journals. Location IDs are also multiplayer room IDs. Update the native Destinations.h, Waters.h, art, browser catalog and fixtures together when changing schemas. Scenery is drawn from the same C++ source on the browser and handheld. When editing Landscape.h or ScenicRecipes.h, recompile the web scenery module from the repository root before running the HTML build.

```sh
zig c++ -target wasm32-freestanding -std=c++17 -Oz -nostdlib -fno-exceptions -fno-rtti game/src/landscape.cpp -Wl,--no-entry -Wl,--export=paintPlace -Wl,--export=placePalette -Wl,--export=ambientSpans -Wl,--export=sampleAmbient -Wl,--export-memory -Wl,--strip-all -o game/assets/landscape.wasm
node verification/browser-tests/scenery.cjs
node verification/browser-tests/ambient.cjs
```

The native firmware compiles the renderer directly. Its compile-time recipe count must match the destination catalog. Historical illustrations remain as source art. The interactive page embeds the compact scene module. Render tests use the live engineering geometry.

## Animated scenery

`Ambient.h` samples the same 240 × 160 landscape on the LCD and browser. At Mae Ngat Reservoir, a bamboo raft takes about 95 seconds to cross from offscreen to offscreen and idles out of view before its return. Faster launches take about 53 seconds. The bow, steering pole and trailing wake face the direction of travel. Paper boats follow the local current. Bridge piers, markets and moored boathouses stay on the baked shoreline. Coastal wave crests, stream ripples, breezy reed tips, occasional showers and evening fireflies are selected by habitat, lighting and seed. Weather and craft service are game fiction.

Live mode samples UTC and uses Bangkok local time for lighting and departures. A dusk departure continues across the 20:00 transition. The Chao Phraya night ferry runs with lanterns. Other boats have narrower overnight windows. Returning to a synchronized device or tab samples the current crossing directly. A manual lighting preview uses the simulation clock, and an unsynchronized handheld uses uptime. All periods used by the travel clock divide its 32-bit rollover interval.

The browser retains its base plus a 1,024-byte command buffer. The LCD writes each span directly to its existing framebuffer, using its existing PSRAM background cache and about 150 bytes of persistent palette/layout metadata. No animation frames ship. The complete scenery WASM is 25,664 bytes. Six RGB captures serve as golden fixtures. The automated suite also samples 31,356 frames and checks that each of 117 places retains distinct geometry in every lighting period. To compare the host-compiled RGB565 LCD path against the browser, pass an empty output directory and the host executable to the test.

```sh
c++ -std=c++17 -O2 verification/browser-tests/ambient-native.cpp -o ambient-native
node verification/browser-tests/ambient.cjs ./capture ./ambient-native
```

This compares 936 full frames, including native 2 × 2 pixel expansion. Physical LCD refresh speed and power consumption still require board measurements. The [capture sheet](../verification/browser-tests/ambient-review.png) shows the same daytime raft at three points in its crossing, alongside three other locations and lighting periods.

The HUD, scene captions, settings, journal and simulator use the bundled Atkinson Hyperlegible Next variable font. The build embeds the font and the two-note WAV speaker check for offline play. The font license is in `assets/fonts/OFL.txt`.

## Cast contact and salvage fixtures

The phone and ESP32 share CastWater.h and Creek.h. Game coordinates are fractions of the complete landscape LCD. Aim is clamped to X 0.08–0.92 and Y 0.555–0.875. The center lane is safe. Habitat changes cover size and shape. The stable destination seed chooses banks, and the period shifts the effective strike zones. Each cast resolves once at splashdown. A visible branch loads the rod until the player eases for half a second and lifts. A rock holds until the player lowers the rod and lets out 0.30 turns. Overwinding can snap the line. A successful release returns to the fishable float. Salvage takes 1.00–1.81 forward turns and awards zero fish, event catches or tackle points.

First casts at Mae Ngat Reservoir at dawn expose repeatable test cases. Aim at the debris center using zoneX(3) and zoneY(3). Seeds 9, 11, 19 and 2 return the sandal, tangled line, dented cup and torn float, respectively. Seed 1 passes through to fishable water. In clear water away from the center, seed 36 at (0.88, 0.85) retrieves accidental salvage. The designed encounter probabilities are 72% at the debris core, 38% at the edge, 4% in off-center clear water and zero in the protected center channel.

Transient phases 7, 8 and 9 represent snag, salvage hauling and salvage landed. The stable journal format and phases 0–6 are preserved. The existing sensor and encoder tick carries lift and signed turns. After placing a snag, the first haptic update requests the existing bottom-hold pulse. Freeing the line issues one lighter tap. Salvage applies one pull on attachment and one light tap on retrieval.

~~~sh
python game/build-engine.py --zig /path/to/zig
node verification/browser-tests/cast-water.cjs
zig c++ -std=c++17 -O2 firmware/tests/cast_water.cpp -o cast_water
./cast_water
~~~

Use Zig 0.13.x. The browser fixture instantiates the actual compiled game and checks its existing imports, location reset, calibrated pose, negative encoder crossings, scrap recovery, journal retention and seeded probabilities. Rebuild the packaged HTML with game/build.py after changing the engine.
