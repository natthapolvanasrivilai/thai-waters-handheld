# Current prototype purchasing

The [R0009 full prototype BOM](R0009-prototype-budget.csv) gives the source, quantity, unit price and allocated cost for each of 74 references. Use the [purchasing and design identifiers](R0009-buy-make-bom.csv) for ordering or fabrication and the [source register](R0009-source-evidence.csv) to check part numbers, controlled drawings and outstanding selections. The [private cost review](../../docs/wiki/BOM-and-business.md) covers a single build and the proposed retail price.

## Historical Rev F purchasing and cost review

**Decision basis, 19 November 2026.** Use the workbook for RFQs and pilot pricing. The 54 buy/make lines cover four sellable configurations with an assembled Waveshare controller. Every unit includes the internal rod receiver, a short USB data cable, retail pack, serialized label and bilingual start card. RUMBLE adds the driver, motor, mounting material and four branch conductors. ROD adds the slide-on rod grip, screw keeper, captive socket screw, hex key and sleeve. FULL includes both options.

## Working files

| File | Purpose |
|---|---|
| [Production cost workbook](Riffle-Rev-F-production-costs.xlsx) | Edit blue inputs. Run costs calculates full manufacturing cost. Channel margins carries Thai direct, US direct and wholesale realization through contribution and program recovery. |
| [Bill of materials](rev-f-buy-make-bom.csv) | Reference, variant, exact purchasing code or candidate process, installed quantity, unit and USD price at each run size. Supplier, purchasing unit and release action appear on the same line. |
| [Print runs](print-estimates.csv) and [part allocations](printed-parts-allocation.csv) | Actual sliced plate grams, time, number of printed parts and SHA-256 hashes of the STL inputs. |
| [Touch-time budget](operation-times.csv), [factory and sales assumptions](manufacturing-cost-drivers.csv) and [NRE](nre-allowances.csv) | Unquoted planning inputs for pilot, small series and a thousand-unit run. |
| [Cost summary](commercial-summary.json) | Baseline snapshot used in the engineering viewer. Changes made in Excel recalculate the workbook; publish a new reviewed snapshot when changing the commercial baseline. |
| [Module boundary](module-boundary.md) | Contents and procurement evidence for purchased subassemblies. |
| [Launch and pricing](../../commercial/launch.md) | Suggested price experiments, pilot objectives and channel economics. |

**Price basis.** Published prices use the supplier's applicable quantity tier for the model lot. The cable, cell, motor, driver and encoder carry Adafruit's 100+ bracket through to 1,000 units. The power switch uses the published 500-piece bracket for the 1,000-unit case, as the next price break is 1,500. The $32.56 A1 reference is a US distributor listing that includes US tariffs. It is a conservative purchasing reference for Thai assembly until a direct price, Incoterm and destination landed quote are in hand. A budget on a supplier-linked row is an engineering allowance. The linked vendor or product family identifies an RFQ route. Minimum spool purchases, packaging die charges and supplier inventory require a purchasing plan and cash forecast before order placement. Fractional metres and grams report unit consumption.

**Engineering changes from the prototype estimate.** The [prototype BOM](../parts.csv) remains the historical bench baseline. Production includes a new four-core branch for the haptic board, a boxed USB cable, consumables by function, product packaging and a hex key with the handle. Confirm connector mating and the four-wire branch join, mechanical restraint for every PCB and loom, shell closure, LED visibility, battery service and the delivery form of each module on the first built units. Any fasteners, inserts, adhesive pads or bracket introduced by that build require a new drawing, line cost and clearance review.

## Factory assumptions

Both plates were sliced in Bambu Studio 02.08.02.61 for an A1 with 0.4 mm nozzle, 0.20 mm layers, five walls, 35% gyroid, generic PETG and tree support. The nine core objects used 61.85 g and 3 h 12 min. The two rod accessory objects used 38.72 g and 1 h 51 min. Individual line costs allocate the complete plate mass by each object's labeled positive XY extrusion. Per-part estimates share purge and support overhead. The clock applies once to each complete plate. The printed color scheme and any second-color purge or dedicated color plates remain to be qualified. Require a dry-material fit build and record actual time, power, parts rejected and grams issued. [Actual STL set](../../hardware/mechanical/rev-F/README.md)

The scenario assumes additive manufacturing in Thailand at each volume. Costs change with published price breaks, labor time, allocated inbound logistics and expected yield. The model charges full replacement cost for each failed build and assumes no salvage credit. A FULL build at 1,000 shipments occupies 10.33 printer-months with 70% uptime and 97% good yield. Eleven A1-equivalent printers running that month would cover the modeled occupancy. Validate queue time, colors, material replenishment, inspection and changeovers before promising delivery.

The $34,000 development, fixture, lab and launch reserve is a planning assumption for the Thai and US program. EU entry, injection molds, distribution partner onboarding, licensing, taxes on business profit and financing are outside the scenario. Unit cost omits engineering NRE until the explicit allocation line. Customer-paid outbound parcel postage is modeled at cost. Requote the lithium-shipping route, duty classification and recoverable input tax before approving either market price.

## RFQ handoff

1. Request revision-locked module quotes and committed quantity breaks for 100, 500 and 1,000 sets with lead time, substitutions, last-time-buy policy, incoming inspection and a sample from the offered lot.
2. Quote the protected pack using its exact cell and protection revision, quantity, protection specification, maximum dimensions, charger limit, shipment state, packing and lot-matched transport documentation.
3. Give fastener suppliers the fit envelope, polymer/pilot and test loads with the request. H2, H3, H4, H5 and H6 still require final part selection. H1 is a screened candidate. Gauge all heads, washers and protruding tips before freezing a purchase code.
4. Send the switch carrier Gerbers and cut-length/termination drawings to the board and harness suppliers. Request assembled harness samples, electronic test evidence, panel MOQ, setup fee, and per-piece price at each volume.
5. Give the box converter the measured packed dimensions and drop/abrasion acceptance criteria. Request a sample that protects the display and retains the loose key. Quote Thai/English print, regional marks and serial traceability with the converter.
6. Replace workbook allowances with supplier quotes and time studies. Record RFQ number, currency, quantity, expiry, Incoterms, lot and approved component revision before procurement release.
