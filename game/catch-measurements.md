# Catch measurements

At 12 cm, the Thai Andaman yellowstripe scad equation predicts **20.5 g**. The Lempake three-spot gourami equation predicts **26.6 g** at the same length. A 19 g catch is plausible for a small fish. [Thai scad survey](https://www4.fisheries.go.th/local/file_document/20170120175615_file.pdf) · [Lempake gourami survey](https://doi.org/10.32491/jii.v21i3.588)

| Card label | Endpoints | Game interpretation |
| --- | --- | --- |
| Total length | Front of fish to tip of tail | Used for 49 of the original 52 entries and most national field-book entries. |
| Body length | Prawn rostrum tip to telson tip | Excludes claws and antennae. The published fit uses millimeters. The field book converts it to centimeters and extrapolates to the largest game prawns. [Prawn survey, figures 3–4](https://seafwa.org/sites/default/files/journal-articles/PERRY-215-222.pdf) |
| Disc width | Maximum straight-line width across the ray | The original freshwater stingray model uses a fit from nine specimens. At 200 cm it gives about 260 kg. New encounters with this species reach 200 cm disc width. A documented Cambodian ray weighed 300 kg at 220 cm across. [Disc-width study](https://doi.org/10.26107/RBZ-2022-0030) · [Cambodian measurement](https://doi.org/10.3390/w15101936) |
| Eye to fork | Sailfish eye to fork of tail | Excludes the bill. The source regression covered 86–188 cm. Game estimates above 188 cm are extrapolations. [NOAA relationship](https://repository.library.noaa.gov/view/noaa/4789) · [IOTC size range and units](https://iotc.org/WPB/24/Data/08-SFSFA) |

For the original 52 entries, eleven relationships come from species-specific population fits and two use a reported size and weight with cubic scaling. Each field-book row identifies the published numerical facts used. Confidence falls when applying a single pond, river, ocean, sex or size range to another population. The two single-point calibrations have greater uncertainty. [Original coefficients and source links](content/Field-book.csv) · [Mekong dai survey and data](https://doi.org/10.5061/dryad.dr7sqvb5h)

The other 39 original species use 21 independently authored shapes. Each row lists three effective body diameters as fractions of total length. Multiplying those diameters by length, taking the ellipsoid volume, and assuming one gram per cubic centimeter gives the estimate. The body dimensions are approximate game-design values. A narrow barracuda and a deep-bodied trevally therefore have different masses at the same length. The national expansion uses authored reference weights and cubic scaling, including the eight fictional animals. These entries have low confidence as real-world mass predictions. [Original shapes](content/Field-book.csv) · [Expansion parameters](content/expand_atlas.py)

The handheld and browser read the same original table and share the same integer scaling for expansion animals. A deterministic 90–110% condition adjustment gives virtual specimens some variation. The adjustment has no statistical confidence level attached. Species, size and prior per-species journal count determine the adjustment once at landing. Waiting, filing or reloading through the same model preserves the catch's weight.

Older journals retain their saved counts and best sizes. They recorded centimeters without a length convention. A previously held 201–240 cm ray therefore shows **Recorded size** and **Unweighed** when restored. Historical rays inside the current size range are indistinguishable in the older save format.
