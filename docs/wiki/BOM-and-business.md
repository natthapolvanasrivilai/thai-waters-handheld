# Prototype sourcing and cost

**R0004 enclosure.** Fit two rear bezel screws and one shelf screw. The optical stack consists of one clear printed diffuser and one Kingbright RGB package. The RGB carrier and drive electronics are under development. The prior blue USB circuit is superseded for this application. [Current BOM changes](../../sourcing/production-intent/Enclosure-R0004-delta.csv) · [Combined PCB baseline](../../hardware/electronics/case-board-r0001/bom.csv)

The archived R0017 A4/A5 mounting allowance covers six insulating blocks and twelve adhesive interfaces. Block stock, adhesive part numbers, process and cost remain unqualified. PETG in the print kit is for test gauges. [Mounts and board functions](../../hardware/mechanical/pcb-fit-display-r0002/README.md)

**R0016 housing.** The indicator entrance and retaining lip are printed into Plate 1. The PCB gauge and purchased parts carry over. Qualify the wired installation and retention before setting a production labor allowance. [Print record](../../hardware/mechanical/TW-A-0001-R0016/Printing/README.md)

**R0015 housing.** The key-bay relief uses the existing cap, retainer and electronics and adds no purchased item. [R0015 build record](../../hardware/mechanical/TW-A-0001-R0015/README.md)

**R0014 housing.** One revised printed housing includes the two A3 seats. The earlier dry-fit strips and die-cut support pads are omitted at A3. Six loose printed spacers remain on the PCB gauge plate for A4 and A5. Bond material, application and retention still require qualification before costing a production process. [R0014 build record](../../hardware/mechanical/TW-A-0001-R0014/README.md)

**R0012 service study.** The [CviLux interconnect and board changes](../../sourcing/production-intent/R0012-interconnect-delta.csv) supersede the Würth haptic header, plug and terminated leads in the historical budget. Cavities 1, 3, 4 and 5 take contacts. A4 and A5 have separate population definitions. Prototype sample prices, harness tooling and delivered board costs are open. Applying the earlier total to this configuration would understate those unknowns. [Historical R0011/R0004 budget](../../sourcing/production-intent/R0011-R0004-BOM.md)

[Wiki contents](Home.md) · [Hardware and cable routing](Hardware-and-3D.md) · [Download the live handbook](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0009-complete-fit-1/Thai-Waters-handbook.html)

## Historical R0011/R0004 engineering BOM

[Read the R0011/R0004 build and procurement basis](../../sourcing/production-intent/R0011-R0004-BOM.md) · [Download the one-unit engineering BOM (CSV)](../../sourcing/production-intent/R0011-R0004-engineering-BOM.csv) · [Thailand-first current quotes (CSV)](../../sourcing/production-intent/R0011-R0004-market-snapshot.csv).

The known fully optioned materials allocation is **$123.29 before unpriced electrical ECO, labor, freight, duties and VAT**. Not a landed total. R0011/X1C is an inert fit print; R0004 powered build and procurement release remain on hold. R0010 and earlier figures below are historical.

## One fully equipped R0009 unit

The full prototype includes the 3.5-inch capacitive display and controller, a protected 1,200 mAh pack, the reel, detachable rod, speaker, motor and driver, three status lights, a data cable, packaging and a 32 GB card for the full artwork library. The optional rechargeable RTC backup cell still needs a qualified part and clearance check.

| Group | Allocated USD for one |
|---|---:|
| Controller, battery, AS5600 and reel magnet | 48.86 |
| Speaker, haptics and mounting materials | 11.16 |
| Wiring, power key, status indicators and consumables | 11.34 |
| Fasteners and handle hardware | 6.72 |
| 16 printed pieces, 80.27 g of material | 2.01 |
| Pack and Tensility USB data cable | 11.95 |
| 32 GB microSD | 19.99 |
| **Materials** | **112.03** |
| Assembly, printer occupancy and electricity | 34.55 |
| **Assembled before freight, tax and qualification** | **146.58** |

Assembly budgets 2.5 hours at $12/hour. The single-material slices total 5.93 printer-hours. At the project's planning rate of ฿35/USD the assembled full prototype is approximately **฿5,130**. A stocked workshop should allow **$152–227** of procurement cash including estimated freight and small-order/setup costs, before tax and labor. A first purchase from an empty workshop depends heavily on supplier packs. Four stock categories alone exceed $560 at the chosen pack sizes. The model excludes shop gauges, multicolor purge, certification and scrap; actual local quotes and a physical build remain open. [74-line BOM with quantity, unit price, extension and supplier](../../sourcing/production-intent/R0009-prototype-budget.csv) · [Source evidence by reference](../../sourcing/production-intent/R0009-source-evidence.csv) · [Cost assumptions and checkout exclusions](../../sourcing/production-intent/R0009-budget.json)

## Selling price

Test the full set at **฿5,490 direct in Thailand** including the model's VAT allowance, or **US$169 direct in the US** before sales tax. These are proposed price points. No paid demand or R0009 production margin has been established. Test willingness to buy after a hands-on reel and rumble demonstration. Track price-shown registrations and interest by fishing clubs versus handheld collectors. [Launch plan and pricing research](../../commercial/launch.md)

The original 100-unit Rev F study projected ฿949.15 or $35.44 contribution per direct sale. A sensitivity check at the same prices and channel assumptions shows a $10 cost increase consumes ฿350 or $10 of that contribution. Reprice the speaker, exact cable, card, harness, print time, yield and freight at the intended lot size before committing to a retail or wholesale price. [Historical Rev F workbook](../../sourcing/production-intent/Riffle-Rev-F-production-costs.xlsx)
