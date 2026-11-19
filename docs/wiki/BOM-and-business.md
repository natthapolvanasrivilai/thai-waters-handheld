# Prototype BOM and selling price

[Wiki contents](Home.md) · [Hardware and cable routing](Hardware-and-3D.md) · [Interactive handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-hardware-review-1/Thai-Waters-handbook.html)

## Pricing scope

The last covered-housing estimate was $112.06 in allocated materials and $146.65 assembled for R0010. R0011 changes the housing toolpath and material use. The R0004 electrical changes require a revised parts allocation and assembly cost once the fitted circuit is established. Use the historical figures for budgeting only. [R0010 cost model](../../sourcing/production-intent/R0010-budget.json) · [Hardware gate](../../quality/hardware-gate.md)

The proposed haptic connector uses one Würth header ($1.15), one housing ($0.18), and four factory-crimped leads ($2.50 each), totaling **$11.33** before freight and tax. This is a replacement subassembly. The whole-unit delta also depends on removed wiring, assembly labor and electronics still under review. Distributor availability needs confirmation at checkout. [Exact part numbers, quantities and US prices](../../sourcing/production-intent/R0004-haptic-terminal-candidate.csv)

The R0011 housing consumes 4.70 g more PETG than R0010, adding $0.1175 at $25/kg. The five superseded W4 loose-wire allocations totaled $0.0585. Substituting the $11.33 connector set gives a partial materials estimate of **$123.45** for the historical configuration with those two substitutions. The PCB redesign, 1 mm shop-made FR-4 spacer, short underside strap, identification and assembly rework still need pricing. [Housing slice](../../hardware/mechanical/TW-A-0001-R0011/QA/print-audit.json) · [R0010 line items](../../sourcing/production-intent/R0010-prototype-budget.csv)

## Electrical procurement candidates

[Exact part-number sourcing index](../../sourcing/production-intent/R0004-candidate-part-links.csv) · [Candidate quantities, installation and engineering sources](../../hardware/electronics/integration-r0004/bom-delta.csv). Selection and layout of the remaining controller logic are open. A production unit quote depends on the completed board.

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
