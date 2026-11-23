# Print the revised key housing

Open the [editable R0015 X1 Carbon project](Thai-Waters-R0015-PCB-Fit-X1C.3mf) in Bambu Studio. If you already have the R0013 or R0014 fit kit, **select plate 1 only**. Reuse the cap, retainer and key gauge. The R0015 housing also includes the two A3 floor rails. [Dry-fit sequence](../README.md)

Plate 1 uses the saved receiver-down orientation, a 0.4 mm nozzle, 0.20 mm layers, opaque PETG in slot 1 and the SuperTack plate. The saved profile commands a 255 °C nozzle and 70 °C bed and uses automatic normal supports with no housing brim. The seven-plate run estimated **2 h 6 min and 53.95 g** for the housing. The other six plates keep their object positions and settings. [Plate contents and other materials](../../TW-A-0001-R0014/Printing/README.md)

After cooling, clear support from inside the key pocket and around the outer button hole. Check the two sides of the switch entry, the internal flange recess and the board grooves for strings or debris. The small end of the cap should be visible in the opening when the flange sits against the inside shoulder. Check the unpowered assembly for binding and cap retention before trying a real switch. The physical fit and switch return still need an actual print. [Cap clearance](../QA/power-key/cap-path.json) · [Board and keeper clearance](../QA/power-key/key-path.json)

## Digital print checks

Bambu Studio 02.09.01.70 sliced all seven plates. The audit found model paths for all 33 expected instances. A separate reopening of the editable project reproduced the switch relief and the A3 rail witnesses on plate 1. All 86,192 housing triangle faces matched the registered STL. The first layer has one connected 776.24 mm² housing footprint. The existing support-started ledge at the USB end also needs care during cleanup. [Project and local extrusion checks](QA/project-check.json) · [Seven-plate result](QA/native-all.json) · [Independent plate-1 result](QA/native-reopen.json) · [Plate-1 native preview](QA/plate-1-reopen.sliced.3mf)

The check measured the deposited bead footprint on both sides of the switch entry, at every model layer from installed Z17.0 through Z27.8 mm. Each 0.60 × 0.14 mm test area was filled in R0014. In R0015 each stayed clear of model and support across all 55 layers. Both 0.60 × 0.34 mm wall areas immediately behind the relief retained their full model footprint. These small areas check that the manufacturing paths follow the specified change. The assembly-motion result covers the nominal 3D route.

## Reproduce the project

From this directory, with the repository CAD Python environment and a fresh scratch directory, run the following commands. The native slice writes local files.

```text
python prepare.py --slicer "/path/to/bambu-studio" --scratch SCRATCH
python verify.py SCRATCH
```

The source of the plate-1 mesh is the [R0015 housing builder](../build_key_housing.py). [Mesh](../Print/housing-battery-bay.stl) · [CAD comparison](../QA/housing-geometry.json)
