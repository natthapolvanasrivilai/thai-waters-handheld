# Inert pack gauges for the Rev F trial housing

Print both files in millimetres at 100% scale with their broad faces on the build plate. The models contain no battery, contacts or energized parts. Use a dimensionally stable filament and gauge the cooled prints with calipers. Record X/Y/Z, material, machine and settings. A measured part within 0.10 mm of each target is a proposed shop screening criterion; final release requires the contracted supplier tolerances and production process capability.

| Gauge | Maximum width × end-to-end length × thickness | What it represents |
|---|---:|---|
| PKCELL-max-body-with-wire-sockets | 35.30 × 62.30 × 5.30 mm | Upper limits of the product-linked QA.S.0228 edition A drawing, rectangular envelope. Two Ø1.60 mm sockets accept loose insulated wire specimens for dressing. |
| Adafruit-258-CAD-with-PCM-and-stubs | 37.00 × 63.00 × 6.00 mm | Separate supplier CAD interpretation. Integrated protection cap and short rigid lead stubs preserve the vendor shape. Body length excluding the stubs is 60.00 mm. |

1. With external power and the real cell disconnected, close the empty case on the gauge only as far as it seats freely. Record any rocking, witness marks, localized compression or interference at the fences, frame and lid. Stop if the bezel or cell surrogate is loaded.
2. For the drawing gauge use two flexible, insulated 24 AWG wire specimens. Allow **100 mm free beyond the gauge face** and record the actual outer diameter. Seat the specimens in the sockets, dress the service loop to the PH connection and observe the full board/lid insertion. The released review route assumes 1.40 mm outer diameter. Check terminal polarity independently on an incoming pack.
3. Record observations for both gauges on the open and closed fit, the lead exit, PH connector and splice sleeves. Store pictures and caliper results with the unit build traveler. Record the minimum actual gap without pressing on the pack.
4. Inspect production lot samples and the vendor-controlled maximum storage/end-of-life swelling envelope separately. These inert shapes test static fit. They cannot establish pouch pressure, swelling, cable bend fatigue, shock, thermal behavior or electrical performance.

CAD predicts interference for the drawing-maximum and alternate vendor-CAD gauges at the current centered position. Keep the production enclosure open for change until the ordered cell is identified, the housing and harness agree with its controlling drawing, and physical fit is signed off. The gauges are independent of the frozen Rev F print set.

[Adafruit product specification](https://www.adafruit.com/product/258) · [PKCELL drawing, page 5](https://cdn-shop.adafruit.com/product-files/258/C101-_Li-Polymer_503562_1200mAh_3.7V_with_PCM_APPROVED_8.18.pdf) · [Adafruit STEP model](https://github.com/adafruit/Adafruit_CAD_Parts/tree/main/258%201200mAh%20lipo)

The supplier CAD portion uses the included Adafruit MIT license.
