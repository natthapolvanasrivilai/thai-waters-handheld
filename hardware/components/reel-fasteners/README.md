# Purchased reel fasteners

| Ref | Orderable part | Model and installed condition |
|---|---|---|
| H2 | [Accu SHP-M2-10-V2-A2-BL](https://www.accu.co.uk/torx-pan-head-screws/475614-SHP-M2-10-V2-A2-BL) | ISO 14583, T6 black A2, M2 × 0.4 × 10. Upper ear Ø2.20 and rotating stem Ø2.14 are clearance holes. Tap M2 × 0.4 in the lower rotor ear only, existing Ø1.70 pilot. Bearing plane Z19.60, new head counterbore Ø4.40. Length from lower thread entry to nominal screw tip is 2.40 mm. |
| H3, two | [OPAC 125N-2](https://www.opac.net/en/producto-581-din-34815-%28din-125%29%2A) | Natural polyamide DIN 125-style, OD5, ID2.2, thickness 0.30 mm. Xem Studio's catalogued M2 nylon washer matches all three supplier dimensions and material. [CC BY 4.0 source](https://www.xemstudio.com/objects/nylon-and-rubber-sealing-washers/) |
| H4 | [Accu SHP-M2-5-V2-A2-BL](https://www.accu.co.uk/torx-pan-head-screws/475608-SHP-M2-5-V2-A2-BL) | ISO 14583 T6 black A2, M2 × 0.4 × 5. Tap the printed stem's Ø1.60 × 5.20 blind pilot, using a bottoming tap and checking full thread depth. The 0.35 mm thrust washer leaves 4.65 mm axial engagement and 0.55 mm nominal tip clearance. |
| H5 | [Accu HPW-M2-A2](https://www.accu.co.uk/metric-flat-washers/72476-HPW-M2-A2) | Plain A2 washer, DIN 125 Form A. ID2.20, OD5.00, 0.35 +0/−0.10 mm. ISO 7089 catalogue CAD matches the supplier's specified dimensions. The axle end seats the washer independently of the moving grip, leaving 0.30 mm nominal end float. |

The helical screw and thrust washer STEP geometry comes from the pinned cq_warehouse standard catalog. Each was instantiated directly with the size and standard in place.py. The STEP thread runout, six-lobe head recess and flat washer are present. [Catalog revision and licence](https://github.com/gumyr/cq_warehouse/tree/a57bb7a24762d367d66369f280a24c38a64e73dd) · [Xem Studio CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Use the supplied placed BREPs for assembly. For the physical prototype, measure the drilled pilots and thread grip, verify H2 seats on the rotor ear and verify stem free-folding and H4 thrust clearance. Record spin drag, back-out or loosening and withdrawal after loaded crank cycling. Replace any printed boss damaged by tapping before testing. Fastener axes run through printed plastic, so retention and lifetime require a physical sample.

* ISO14583-M2x10.step SHA-256 7f8e6740568fc21d1e75d43f9a075596e88f712af92412f5af807d9e6db4877f
* ISO14583-M2x5.step SHA-256 0022f41fa160ca437be41f3a0d0d8d54075f1cdbe42998bbbbc414d68c53ea78
* ISO7089-M2.step SHA-256 47c272210d34932f625b75d5d466de561a2d07739231c99862a1a7f525596a37
* M2-nylon.step SHA-256 2af4fbf24efdcd25669113d15bd9909c86ee13e31ab9edbf7361503cf3d2ec77

The H5 interchange solid uses the two circular radii and thickness of the ISO 7089 catalog model. Rebuilding the annular solid fixes an open periodic seam found during the STEP round-trip test.
