# Simulator source
The owner-private hosted build and phone QR are linked in [Phone playtest](sites/Phone-playtest.md). Phone touch screens start with the full fishing view. The 3D model initializes when the player selects Device view. The hosted `/event` service uses D1 for short-lived scores. Personal catches and tackle stay in each browser.

Open Thai-Waters-play.html directly for offline desktop play. For phone motion and shared events use lan/README.md. Toggle Screen only for an unobstructed gameplay view. On the modeled LCD, tap to cast or lift and tap MENU to navigate. Grab the right-side reel and move the pointer around its projected axle. Fold reel pivots the amber grip into the modeled well. The near-edge green shell, bezel, rotor, grip, collar and retainers come from the mechanical CAD. The Rev F model also includes the top power cap and optional rod grip. Surface finishes are a visualization.

Run python game/build.py from the repository root to regenerate the self-contained viewer from local assets. It has no CDN dependencies. To rebuild the renderer, enter game/src, run npm ci, then npx esbuild play-device.js --bundle --minify --format=iife --outfile=../assets/device-renderer.min.js. The WebAssembly is compiled from firmware/tests/bench.cpp with Zig C++ targeting wasm32-wasi and linked with wasm-ld --no-entry --export-dynamic --allow-undefined --strip-all. Use the functions imported by the packaged viewer. The firmware and browser share the game, pose, wheel and audio code.

Game data lives under content and locations.json. Stable IDs preserve existing journals. Location IDs are also multiplayer room IDs. Update the native Destinations.h, Waters.h, art, browser catalog and fixtures together when changing schemas. Scenery is drawn from the same C++ source on the browser and handheld. When editing Landscape.h or ScenicRecipes.h, recompile the web scenery module from the repository root before running the HTML build.

```sh
zig c++ -target wasm32-freestanding -std=c++17 -Oz -nostdlib -fno-exceptions -fno-rtti game/src/landscape.cpp -Wl,--no-entry -Wl,--export=paintPlace -Wl,--export=placePalette -Wl,--export-memory -Wl,--strip-all -o game/assets/landscape.wasm
node verification/browser-tests/scenery.cjs
```

The native firmware compiles the renderer directly. Its compile-time recipe count must match the destination catalog. Historical illustrations remain as source art. The interactive page embeds the compact scene module. Render tests use the live engineering geometry.

The HUD, scene captions, settings, journal and simulator use the bundled Atkinson Hyperlegible Next variable font. The build embeds the font and the two-note WAV speaker check for offline play. The font license is in `assets/fonts/OFL.txt`.
