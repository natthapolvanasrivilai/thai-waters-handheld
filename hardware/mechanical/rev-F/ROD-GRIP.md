# Rev F detachable rod handle

The handle slides into the back of the handheld from its lower edge. A 35 mm dovetail engages both sides of the receiver. A blind end stop sets its position, and a captive M3 screw pulls the broad grip shoulder against the receiver face. A steel nut takes the thread load. The rounded receiver adds 3.20 mm to the back of the bare unit. Both sides of the screen and the folding reel remain accessible.

## Parts and first assembly

| Part | Quantity | Detail |
|---|---:|---|
| Rev F housing | 1 | The female receiver and the internal hex nut pocket are integral. |
| Rod grip | 1 | Print `Print/rod-grip.stl` in its supplied side orientation. |
| Grip screw keeper and receiver nut keeper | 1 each | Print the two keeper STLs on their flat faces. They retain the fasteners when the handle is removed. |
| Accu SSCF-M3-10-A2 | 1 | M3×10 ISO 4762 socket-head screw, coarse pitch 0.5 mm, 2.5 mm hex drive. |
| Accu HPN-M3-A2 | 1 | M3 ISO 4032 hex nut, 5.5 mm across flats and up to 2.4 mm thick. |

Fit the nut and inner keeper in every base unit during factory assembly. The separately sold accessory includes the handle, screw and grip screw keeper; its owner can attach it with the enclosure closed.

1. Clear support and burrs from the receiver mouth, dovetail flanks, shoulder and tool-access hole. The grip should slide to its stop by hand. Inspect the groove roof after removing any support.
2. With the shell open, drop the nut into its hex pocket. Seat the inner keeper with its central relief facing the nut. Bond the keeper's outer cylindrical rim with adhesive validated for the printed polymer. Keep the thread and nut seating face clean.
3. Insert the screw through the underside of the grip with the socket facing out. Install the ring over the head, leaving the socket accessible. Bond only the ring's outer rim. Allow a full cure and verify that the screw rotates and falls freely through its capture stroke.
4. With the screw withdrawn and the display facing up, slide the grip toward the top edge until it reaches the stop. Use the 2.5 mm key to engage the metal nut and tighten just until the shoulder sits flat and the handle is steady. Inspect for shell distortion. The physical prototype will establish the assembly torque.
5. To remove, loosen until the screw disengages, let it drop back against the keeper, and slide the handle toward the lower edge. The screw and ring travel with the handle. The nut and its keeper stay inside the enclosure.

The separate seated and removal STEP files show both assemblies at these positions. The screw moves along Z and the handle slides along Y. A threaded-envelope model represents screw/nut engagement in the digital assembly.

## Printing and dimensions

The Bambu Studio 02.08.02.61 slice used Generic PETG, a Bambu Lab A1 with a 0.4 mm nozzle, 0.20 mm layers, five walls, 35% gyroid and automatic tree support. The **accessory-only** handle and screw keeper plate used **38.72 g** including support and **1 h 50 min 45 s**. Adding the factory nut keeper brings the plate total to 38.76 g and 1 h 50 min 55 s. The three printed parts account for 36.82 g. These estimates exclude the receiver housing, metal parts and adhesive.

| Interface | Nominal geometry |
|---|---|
| Male dovetail | 35 mm engagement, 24.98 mm head width, 19.04 mm neck width |
| Running clearance | 0.378 mm horizontally per flank, approximately 0.295 mm normal to the flank. Unclamped lateral travel is approximately 0.76 mm total. |
| Receiver | 35.8 mm overall width, 3.2 mm proud of the former rear plane, 1.70 mm continuous roof under the central groove away from the screw clearance bore |
| Shaft / head | Ø3.56 mm grip bore, Ø3.60 mm case bore, Ø6.24 mm head chamber, Ø3.70 mm keeper access |
| Nut / mechanical stop | 5.88 mm across flats in the nut pocket, 5.30 mm head retraction allowance |

The face clamp is intended to remove operating rattle. Measure actual play on the printed pair. Printer shrinkage, elephant foot, thread chamfers, layer direction, clamp force and wall creep can all affect the result. Check thread engagement and the tip-to-keeper gap on the purchased screw and nut.

## Verification and physical acceptance

`rod-grip-checks.json` records the static clearances, 44 slide positions at 1 mm spacing, 21 screw positions through the retraction stroke, and two sample tolerance offsets. A locked screw encountered solid housing under reverse sliding, a rigid pull at the undercuts encountered both rails, and the end stop blocked overshoot. The model checked the optional driver, motor, protected cell, service openings and a conservative moving reel envelope. The coordinated populated housing and power key checks are in `checks.json`.

For a first **unpowered** fit print the proposed proof target is 1.0 N·m about each transverse joint axis. At a 112 mm arm, a 9 N grip-tip load produces approximately 1.0 N·m. A 35 mm ideal bearing couple gives about 29 N of reaction; actual pressure concentrates at the ends. A 20 mm transverse couple gives about 50 N. These are fixture sizing calculations. They do not establish the joint's strength.

- Witness-mark the screw, rail and housing. Record initial free play and the assembly torque with a torque driver. Hold the case in a padded fixture with the receiver faces free.
- Apply 9 N in alternating transverse directions at the measured grip lever arm for 10 seconds per direction. Check for cracking, disengagement, torque loss and permanent tip offset. The proposed maximum residual offset is 1 mm after unloading.
- Pull 30 N along the slide-out axis for 10 seconds with the screw engaged. Inspect the blind stop, nut seat, rail roots and keeper retention.
- Repeat the fit and load checks after 100 detach/reattach cycles. Record thread condition, shake noise, free play and removal force before deciding on print settings or a production torque.

All three print files passed single-body, watertight mesh checks. Printing, load capacity, wear, screw torque and comfort in a physical grip remain open.
