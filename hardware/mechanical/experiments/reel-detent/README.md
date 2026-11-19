# Reel detent feel coupon

Print the wheel and one frame to compare a physical reel click with the simulated reel. This standalone bench assembly uses the Rev E crank leverage. Twelve rounded lobes give one click per 30° in either direction. It uses three printed parts to compare both spring strengths and requires no fasteners, batteries or magnets.

## Print and assemble

1. Start with `wheel.stl` and `frame-light.stl`. The files are oriented for a flat bed. A starting setup for this trial is PETG, a 0.4 mm nozzle, 0.20 mm layers and solid thin walls. The spring flexes in the layer plane. Check the sliced spring for continuous wall paths at its root.
2. Remove any first-layer flare around the wheel bore and axle. Put the frame flat on a table, press the small rounded follower gently outward and lower the wheel onto the central peg. The wheel rests on the circular shoulder, with its finger post pointing up. The wheel lifts off for changes. Keep the fixture flat while testing.
3. Hold the thick rear spine. Turn the finger post through one full revolution each way. Count twelve clicks. Try slowly creeping across one crest, then winding continuously. Check for sticking, skipping and contact between the wheel and rigid frame.
4. Print `frame-firm.stl` and repeat with the same wheel. The light spring is 1.2 mm thick and the firm spring is 1.6 mm thick. Record the preferred material, slicer settings, breakaway feel and acoustic level for both directions. Inspect the spring root and follower after repeated cycling.

## Geometry and integration

| Feature | Nominal dimension |
|---|---:|
| Rev E crank throw, reproduced on coupon | 7.80 mm |
| Cam crest radius, matching Rev E rotor radius | 12.75 mm |
| Cam valley radius | 12.15 mm |
| Axle diameter / wheel bore | 9.10 / 9.70 mm |
| Centered follower deflection, valley to crest | 0.38 to 0.98 mm |

The coupon reverses the bearing arrangement to allow tool-free wheel changes. Its stationary axle and rotating bore preserve the Rev E nominal radial clearance of 0.30 mm. The legacy rotor turns with a shaft in the stationary housing. The Rev E well has only 0.60 mm between the smooth rotor and the wall. Transferring this mechanism to a handheld requires a dedicated spring pocket and an updated cam rotor, followed by assembled fold, wear, sensor-gap and pocket-noise tests.

`build.py` generates the three watertight STL solids, an exploded light-frame STEP and `checks.json`. The analytical cam check samples every 0.5° through a full rotation and confirms twelve equally spaced crests. A full rotational envelope checks the cam against the rigid frame. Spring contact is intentional. Actual spring force, sound, lifetime and print clearance still require a physical test. A passive spring stays audible with electronic cues muted.
