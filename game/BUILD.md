# Simulator source
The owner-private hosted build and phone QR are linked in [Phone playtest](sites/Phone-playtest.md). Phone touch screens start with the full fishing view. The 3D model initializes when the player selects Device view. The hosted `/event` service uses D1 for short-lived scores. Personal catches and tackle stay in each browser.

Open Thai-Waters-play.html directly for offline desktop play. For phone motion and shared events use lan/README.md. Toggle Screen only for an unobstructed gameplay view. On the modeled LCD, tap to cast or lift and tap MENU to navigate. Grab the right-side reel and move the pointer around its projected axle. Fold reel pivots the amber grip into the modeled well. The near-edge green shell, bezel, rotor, grip, collar and retainers come from the mechanical CAD. The Rev F model also includes the top power cap and optional rod grip. Surface finishes are a visualization.

Run python game/build.py from the repository root to regenerate the self-contained viewer from local assets. It has no CDN dependencies. To rebuild the renderer, enter game/src, run npm ci, then npx esbuild play-device.js --bundle --minify --format=iife --outfile=../assets/device-renderer.min.js. The WebAssembly is compiled from firmware/tests/bench.cpp with Zig C++ targeting wasm32-wasi and linked with wasm-ld --no-entry --export-dynamic --allow-undefined --strip-all. Use the functions imported by the packaged viewer. The firmware and browser share the game, pose, wheel and audio code.

Game data lives under content and locations.json. Stable IDs preserve existing journals. Location IDs are also multiplayer room IDs. Update the native Destinations.h, Waters.h, art, browser catalog and fixtures together when changing schemas. Scenery is drawn from the same C++ source on the browser and handheld. When editing Landscape.h or ScenicRecipes.h, recompile the web scenery module from the repository root before running the HTML build.

```sh
zig c++ -target wasm32-freestanding -std=c++17 -Oz -nostdlib -fno-exceptions -fno-rtti game/src/landscape.cpp -Wl,--no-entry -Wl,--export=paintPlace -Wl,--export=placePalette -Wl,--export=ambientSpans -Wl,--export=sampleAmbient -Wl,--export=arrivalDuration -Wl,--export=arrivalLanding -Wl,--export=arrivalPixels -Wl,--export=arrivalShapes -Wl,--export=sampleArrival -Wl,--export-memory -Wl,--strip-all -o game/assets/landscape.wasm
node verification/browser-tests/scenery.cjs
node verification/browser-tests/ambient.cjs
```

The native firmware compiles the renderer directly. Its compile-time recipe count must match the destination catalog. Historical illustrations remain as source art. The interactive page embeds the compact scene module. Render tests use the live engineering geometry.

## Animated scenery

`Ambient.h` samples the same 240 × 160 landscape on the LCD and browser. A seeded route offers one daytime vessel crossing per roughly 4.4-minute slot. Departure and speed vary independently of fishing RNG. Launches take about 33–41 seconds, while rafts and sailboats take about 45–53 seconds. Each vessel crosses one way and exits fully; its quiet engine/wake sound follows the visible pass, not the music. The bow, steering pole and trailing wake face the direction of travel. Paper boats follow the local current. Bridge piers, markets and moored boathouses stay on the baked shoreline. Coastal wave crests, stream ripples, breezy reed tips, occasional showers and evening fireflies are selected by habitat, lighting and seed. Weather and craft service are game fiction.

Live mode samples UTC and uses Bangkok local time for lighting and departures. A dusk departure continues across the 20:00 transition. The Chao Phraya night ferry runs with lanterns. Other boats have narrower overnight windows. Returning to a synchronized device or tab samples the current crossing directly. A manual lighting preview uses the simulation clock, and an unsynchronized handheld uses uptime. All periods used by the travel clock divide its 32-bit rollover interval.

The browser retains its base plus a 1,024-byte command buffer. The LCD writes each span directly to its existing framebuffer, using its existing PSRAM background cache and about 150 bytes of persistent palette/layout metadata. No animation frames ship. The scenery module also exports the vessel sound mix and an optional quiet PCM world layer. It does not modify the shared fishing audio score. Six RGB captures serve as golden fixtures. The automated suite also samples 31,356 frames and checks that each of 117 places retains distinct geometry in every lighting period. To compare the host-compiled RGB565 LCD path against the browser, pass an empty output directory and the host executable to the test.

```sh
c++ -std=c++17 -O2 verification/browser-tests/ambient-native.cpp -o ambient-native
node verification/browser-tests/ambient.cjs ./capture ./ambient-native
```

This compares 936 full frames, including native 2 × 2 pixel expansion. Physical LCD refresh speed and power consumption still require board measurements. The [capture sheet](../verification/browser-tests/ambient-review.png) shows the same daytime raft at three points in its crossing, alongside three other locations and lighting periods.

The HUD, scene captions, settings, journal and simulator use the bundled Atkinson Hyperlegible Next variable font. The build embeds the font and the two-note WAV speaker check for offline play. The font license is in `assets/fonts/OFL.txt`.

## Arrival pacing and transition

Destination changes retain the 4.2-second arrival and 3.33-second rod cue. Footpath, hiking, driving and longtail approaches cruise at 1.20, 0.95, 6.00 and 3.00 m/s. They cover 3.426, 2.712, 17.130 and 8.565 m after easing in through 0.30 s and settling from 2.68 to 3.33 s. Walking camera motion follows step distance rather than a timer; the vehicle uses a firmer suspension motion and the longtail a slower hull heave. The shared indexed renderer reveals the already-rendered fishing bank from 3.03 to 3.76 s under the rod raise. The browser's reduced-motion path is still a 550 ms still, and skipping does not cast.

```sh
c++ -std=c++17 -O2 verification/browser-tests/arrival-native.cpp -o arrival-native
./arrival-native
# Rebuild game/assets/landscape.wasm with Zig 0.13.0 using the command above,
# then regenerate the interactive HTML and run the browser integration check.
python game/build.py
node verification/browser-tests/arrival.cjs
```

## Cast contact and salvage fixtures

The simulator and ESP32 use the same submerged layout from CastWater.h and Creek.h. Each visit rolls for submerged branches, rocks and debris using the destination's terrain and the season. A water can be entirely clear. Structures stay put across casts and changes of light, so a player can avoid a known snag. Returning after travel can yield a new layout. A cast through a debris patch can miss it. Marshes lack rocky outcrops, and exposed Gulf waters lack submerged trees. Each present feature gets a position on either side of the middle channel. Splashdown resolves the contact. To free a branch, stop winding for half a second and lift. To free a rock, lower the rod and pay out 0.30 turns. Salvage takes 1.00–1.81 forward turns and earns no catch or event credit.

At Mae Ngat Reservoir at dawn in the cool season (November to February), seed 1 yields an empty layout. Seed 2 has a branch and seed 5 has a rock. For engine tests, aim at the debris center using zoneX(3) and zoneY(3). Seeds 16, 42, 35 and 10 return the sandal, tangled line, dented cup and torn float respectively. A debris pickup has a 72% chance at its center and a 38% chance at its edge.

Fishing spots offers Seasonal, Clear, Light rain, Heavy rain and Storm. Seasonal uses the Bangkok calendar day, destination and selected time period. The regional game weights reflect the southwest monsoon and the later rain season on the southern Gulf coast. Offline hardware without a synced clock starts with a simulated date. Both renderers use the same animated rain, distant lightning and water glints. Light rain shortens float waits. Heavy rain and storms lengthen them. Rain also lengthens lure pauses and increases tension when winding into a fish's run. The conditions stay fixed during the cast. [Thai Meteorological Department climate overview](https://www.tmd.go.th/en/climate/summarymonthly)

Transient phases 7, 8 and 9 represent snag, salvage hauling and salvage landed. The stable journal format and phases 0–6 are preserved. The existing sensor and encoder tick carries lift and signed turns. After placing a snag, the first haptic update requests the existing bottom-hold pulse. Freeing the line issues one lighter tap. Salvage applies one pull on attachment and one light tap on retrieval.

~~~sh
python game/build-engine.py --zig /path/to/zig
node verification/browser-tests/cast-water.cjs
zig c++ -std=c++17 firmware/tests/cast_water.cpp -o cast_water
./cast_water
~~~

Use Zig 0.13.x. The browser fixture instantiates the actual compiled game and checks its existing imports, location reset, calibrated pose, negative encoder crossings, scrap recovery, journal retention and seeded probabilities. Rebuild the packaged HTML with game/build.py after changing the engine.

## Extended field guide

Build the shared encounter records and catalog indices with `python game/content/expand_atlas.py` before rebuilding the engine. The original 52 IDs stay stable. The next eight are specifically authored fictional species, including five Mythics. Each Mythic needs a specific destination, time window and compatible bait. Later records use accepted scientific names. The field guide exposes their modeled fishing water, size range and preferred bait. These are game parameters. A country-level record alone does not establish occurrence at a particular pier or certify diet, abundance or maximum size. Every catalog record has an individual packed portrait. A handheld without the matching art card retains its resident encounter selection and marks unavailable card images in the field guide. See the [artwork register](art-source/coverage.csv).

The extended species sources are [GBIF](https://www.gbif.org/occurrence/search?country=TH), the [ASEAN Fish Species Collection](https://ipt.aseanbiodiversity.org/resource?r=aseanfishspecieslist), and the [Thai national checklist](https://chm-thai.onep.go.th/wp-content/uploads/2021/09/ONEP_V04.pdf). The ASEAN Centre for Biodiversity publishes its family checklist under CC BY 4.0. The GBIF occurrence queries use records marked CC0. The software stores species names and source references. Expanded catches use family-level gameplay weight estimates; the original 52 use the models documented in [Catch measurements](catch-measurements.md).

The first-person approach uses perspective-projected ground geometry, roadside markers and water detail. Stable destination recipes choose walking, hiking, driving or longtail travel. Browser and handheld rasterize the same 240 × 160 indexed foreground. The path uses perspective-correct ground textures, trees and rushes use pixel sprites, and the boat carries timber grain. The handheld writes directly to the LCD with one 240-byte row of scratch space for rasterization. The 4.2-second sequence hands off to the normal rod view. Tap to skip. Browser reduced-motion mode shows a still for 550 ms.

### Specimen portraits

After editing a source plate or species mapping, run `node game/art-source/compile-field.cjs` and `python game/art-source/coverage.py`, then rebuild the WASM and standalone HTML. The field compiler emits the firmware index, resident pixels and the versioned SD pixel bank. Build the HTML and firmware package against the same generated files. Details and source credits are in the [art register](art-source/README.md).
