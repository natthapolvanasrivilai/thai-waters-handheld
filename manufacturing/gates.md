# Build and release decisions

Record the exact enclosure and electrical integration IDs at incoming inspection, at final test and after rework. The [hardware revision register](../hardware/revisions/README.md) links those configurations to the drawings, print files and change records. The next inert fit is **TW-A-0001-R0007** (Rev G) with **TW-A-0002-R0002** (Rev F wiring). Enter the actual firmware version and digest separately when a unit is flashed. Retain the prior IDs and effectivity when a fielded unit changes configuration.

| Stage | Required record for this handheld | Current status |
|---|---|---|
| Concept | Product requirements, target market, age grade and bill of materials | Initial requirements and prototype BOM available, market scope open |
| EVT engineering samples | Register supplier revision and serial; verify assembly sequence, RF keep-out, reel field, charge polarity, thermal cutoff, clock backup and radio power profile | Nominal Rev E CAD results available, physical results pending |
| DVT design validation | Test production-intent resin or printed material, finish, stack tolerances, folding wear, magnet retention, drops, cable ESD, RF, EMC and battery thermals | Pending materials, engineering samples and lab scope |
| PVT pilot | A lot built with the intended fixture, traveler and workmanship limits. Record yield, rework, calibration and packaging checks | Pending |
| Production release | Baseline an approved drawing, BOM, firmware hash, test fixture, artwork, market reports and signed release record | Pending |
| Sustaining and end of life | Link supplier PCNs, service stock, failure trends, update support and battery recycling arrangements to affected serials | Templates available |

Use the programmable USB connection and exposed screw closure during EVT. Prototype adhesive registration and the hand-spliced battery adapter need process validation. Replace the adapter with a keyed supplier-built harness with controlled pinout before pilot. A move from FDM to tooling changes shrinkage, flammability evidence, drop performance and the reel tolerance stack. Requalify the enclosure.

Create engineering releases from a reviewed commit, identify hardware and firmware independently, and retain the manufacturing lot's as-built record. Duplicate the blank traveler per unit or lot. Keep customer contact details in the authorized service system.
