# R0011 fit print and service

1. Import the supplied housing STL at 100%. Keep its supplied receiver-down orientation. In layer preview, the case cavity opens upward and the first model layer shows both rod-grip lips joined by their closed end. Use generic PETG, a textured PEI plate, 0.4 mm nozzle, 0.20 mm Standard, 30° automatic normal support with support on model enabled, and no housing brim. The tested housing measures 110.72 × 74.25 × 31.00 mm in the supplied pose.
2. Let the plate cool before releasing the housing. Remove support below the broad rear floor, at the reel and from the receiver channel. Start at the open slide entrance and work in sections toward the stop. Avoid levering against the dovetail edges. Clear the separate speaker grille and USB-end details. Inspect for layer separation at both rail roots and for a widened first layer or support residue on the sliding faces.
3. Slide the inert grip fully to the stop by hand, engage the captive fastener and check insertion, retention, play and smooth removal. Record grip-tip deflection at the intended test load, layer cracking, permanent set and wear through repeated attachment cycles. Confirm bezel fit, clean bores and reel travel. Check the two inert cell gauges, covered lower edge, service-probe access and speaker grille before installing electronics. The slicer check establishes the shape of the toolpath. Measured strength and wear remain first-article gates.
4. Print the other 16 device positions, including P17, with their original material and orientations. Follow the R0010 service-cover instructions and R0009 component assembly sequence linked below. Use P17 during normal operation. Peel from the relieved USB end for bench access to the board PWR, RESET and BOOT switches.

[Service cover and installation](../TW-A-0001-R0010/PRINT-GUIDE.md) · [Other print materials and assembly sequence](../TW-A-0001-R0009/PRINT-GUIDE.md)

## Reproduce the print check

From this revision directory in a repository checkout, use Python with NumPy, trimesh, SciPy, Shapely, Pillow and matplotlib and a Bambu Studio installation with the A1 profiles. Supply a fresh scratch folder. The report records both exact STL and G-code hashes.

```text
python build.py
python check_print.py --work <scratch> --slicer <bambu-studio-executable>
python QA/draw_toolpaths.py <scratch>
python package_prints.py --exports <exports>
```
