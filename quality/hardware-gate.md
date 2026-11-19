# Hardware closure before gameplay development

[Private issue tracker](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/1)

**Production and powered-prototype approval are on hold.** The owner requested hardware and electrical closure before further gameplay development. The phone playtest and USB firmware remain at the published [0.9.4 baseline](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/firmware-v0.9.4).

| Hardware finding | Verification needed for closure |
|---|---|
| [Header and wire termination · #2](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/2) | Identify the header, specify and draw both sides of the mating connection, verify pinout, check installation clearances, and test retention and continuity on the assembled harness. |
| [Long support-founded island · #3](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/3) | The former 36.8 × 0.6 mm support-founded strip now starts on the bed with the opposite dovetail lip and closed stop. Support rises from 4.60 g to 11.92 g. Check printed rail strength, fit and wear. [Before/after toolpaths](../hardware/mechanical/TW-A-0001-R0011/QA/receiver-toolpaths.png) · [Print instructions](../hardware/mechanical/TW-A-0001-R0011/PRINT-GUIDE.md) |
| [Electrical limits · #4](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/4) | Link each failing measurement to its original limits, revised hardware and rerun. Preserve fault controls and list bench-only measurements separately. |
| [Exposed service slot · #5](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/5) | R0010 adds a removable opaque cover. CAD measures both wall faces, projected coverage, component clearance and tool access. Pull force, wear and fit require a physical print. [Design and photos](../hardware/mechanical/TW-A-0001-R0010/README.md) · [Geometric checks](../hardware/mechanical/TW-A-0001-R0010/QA/service-cover.json) |

The original [55 circuit measurements](../hardware/verification/circuits/results.csv) and [later load study](../hardware/electronics/usb-status-r0003/simulation/load-results.csv) remain the baseline evidence. The [first-article matrix](../hardware/verification/circuits/bench-matrix.csv) records physical evidence separately from circuit models.

The playtest queue covers the operating 3D device (#6), individual fishing-location thumbnails (#7), rod bend and at-hook tension feedback (#8), variable state-driven encounters (#9), cast impulse and touch charge (#10), and fish-driven payout, line length and fatigue (#11). Each issue has its own acceptance criteria in the tracker.
