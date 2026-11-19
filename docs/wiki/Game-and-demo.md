# Play and evaluate a cast

[Handbook contents](Home.md) · [Repository home](../../README.md) · [Interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/firmware-v0.8/Thai-Waters-0.8-handbook.html)

[Open the private phone playtest](https://thai-waters-pocket-angler.shoung0690.chatgpt.site) or choose **Playable demo → Start playable demo** in the handbook. Tap once to enable audio. On a phone, open the playtest directly in the browser for motion permission. The [phone test guide](../../game/sites/Phone-playtest.md) covers calibration and fallback controls.

The web game opens in Thai. Choose **เมนู → English** or **Menu → ไทย** to change the language on this browser. The rod workshop displays six illustrated baits in the picker. The selected bait also appears on the hook before casting.

1. Open **Fishing spots**, select a different destination and choose **Fish here**. Watch the water approach from your own eye level. Walk down a bank, hike a trail, drive to a landing or ride in the bow of a longtail boat. The rod rises as you reach fishing position. Tap **Skip** to get straight to your rod. Changing the light at the same spot keeps you in place.
2. Tap a patch of water to cast there in the simulator. The central channel is clear. Casting close to cover introduces branch, rock and salvage encounters.
3. If a branch catches the line, stop winding for half a second, then lift. At a rock, lower the rod and pay out at least 0.30 turns. Reel in salvage to identify the object. It earns no fish record or event score.
4. For a fish, follow the float, strike on the bite and respond to the run or bottom hold. Inspect the landed specimen at your own pace. Tap anywhere on the catch card to file it, apply its reward and return to fishing. Open the field book and tackle controls inside the LCD.

Open **Rod workshop** before casting to choose a bait and its presentation depth. Try raw shrimp on the bottom for a river prawn. Floating shrimp cannot reach it. The field book gives each entry a bait tip and lets you search by name. Its 2,545 entries include eight fictional species and five Mythics. The [national checklist notes](../../game/content/national-checklist.md) explain the records behind the real-species roster. The [catch measurement notes](../../game/catch-measurements.md) describe the estimates.

The approach and landscape share the 240 × 160 art grid. Trail gravel, grass and lane markings move in perspective. The longtail’s bow stays under the viewpoint as the water moves past. [Compare four captured journeys](../models/arrival-routes.png).

Try one place at dawn and dusk to see the shift in light and traffic. Select music and bite cues on the sound panel. On iPhone Safari, the audible speaker check and visual tension cues support playtesting. The handheld motor is needed to evaluate complete rumble patterns. Explore the [location catalog](../../game/locations.json), [fish field book](../../game/content/Field-book.csv) and [motion and snag fixtures](../../game/BUILD.md).

**Daily specimen cup.** Open Events & rankings, enter the cup, then choose Fish this water. The board lists the target species, minimum length, host water and your rank. Bigger qualifying catches improve your place. Equal lengths share a rank. The next cup begins at midnight in Bangkok. The hosted phone playtest and the LAN host each keep their own board.

**Fishing conditions.** Choose Seasonal, Clear, Light rain, Heavy rain or Thunderstorm in Fishing spots. Weather changes lure presentation and the fight. Submerged snags occupy some habitats and can be absent throughout a visit. The center channel stays clear.

Tap the water where the cast should land, or use the rod gesture. The four icons underneath the location show the rod finish, technique, bait and fishing depth. Tap the icons to open the workshop. During a fight or snag, the eight-segment tension gauge follows the line end. A high-load warning appears above the gauge.

The collection fills the LCD. Tap a rarity-bordered thumbnail to open its field notes and chronological catch log. Gold identifies Mythic specimens. Undiscovered species show a silhouette and fishing clues. Confirming the first catch reveals the name, portrait and full account. Each new log records measured size, estimated mass, Bangkok date and time, fishing location, period, weather, bait and depth. Older aggregate records keep their original counts and best lengths. The catch confirmation pulses until tapped and stays steady when reduced motion is enabled.

In the Motion bench, enable the handheld controller after pairing **Thai Waters Rod** in phone Bluetooth settings. On the handheld start the controller session, then use the rod and knob to cast, hook and retrieve in the phone game. In the simulator the right wheel supports a circular drag, a center hold or the Auto reel switch. Safari offers system switch feedback on supported iPhones. The handheld motor supplies fishing patterns when fitted.

[Clock retention, journal storage and the cloud restore design](Clock-and-saves.md)

[← Thai Waters product wiki](Home.md) · [Inspect the assembly and battery pocket →](Hardware-and-3D.md)

The native simulator uses 52 LCD pixels (about 8 mm) as its baseline tap target, larger in narrow portrait layouts. The collection shows eight fish per page in two rows of four. Drawer routes and gear choices scroll vertically.

The mobile WebKit hit-test traverses all six menu routes, both navigation icons, catalogue paging and detail, all six bait tiles, Cast, and the controller and audio settings. It scrolls each target into view, checks its center reaches the intended element and measures its projected bounds. Landscape 844×390 and 667×375 measured 63.4 and 57.4 CSS pixels respectively at the smallest tested target. Portrait 390×844 and 320×568 measured 45.7 and 45.6. These are simulated viewport measurements. [Repeat the touch checks](../../verification/browser-tests/finger-targets.cjs)

The rod loads for 180 milliseconds, then the spool pays out before the bait reaches water at 900 milliseconds. Reel click volume controls payout. Effects volume controls the swish, water impact, retrieve splashes and line snap. The tension gauge follows the line where it meets the water.

Use the header arrows for settings, destinations and rankings. The journal displays one catch record per page. Back returns to the same thumbnail page. The national catalog includes 2,536 real fish, the giant freshwater prawn and eight fictional specimens. All 377 species in the field-record expansion have individual painted portraits. The release contains 456 illustrated entries in total. The field-note icon identifies an entry whose illustration is pending. The [additional field records](../../game/content/field-evidence.md) give the sources for the 377 latest additions.
