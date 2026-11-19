# Thai Waters handheld

[Hardware closure and playtest issues](quality/hardware-gate.md) · [Open the private tracker](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/1)

[Private touch playtest](https://thai-waters-pocket-angler.shoung0690.chatgpt.site) · [0.9.4 handheld controller preview](firmware/Phone-controller.md) · [Download the USB prototype](releases/prototypes/Thai-Waters-controller-0.9.4.zip) · [Clock and collection recovery](docs/wiki/Clock-and-saves.md)

[Hardware revisions and CAD](docs/wiki/Hardware-and-3D.md) · [One-unit BOM and price research](docs/wiki/BOM-and-business.md) · [Current release and hardware milestone](docs/wiki/Software-and-tests.md#current-release)

**[Browse the product wiki](docs/wiki/Home.md)** · **[Download the interactive handbook](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/firmware-v0.9.4/Thai-Waters-handbook.html)** · **[Play on a phone](https://thai-waters-pocket-angler.shoung0690.chatgpt.site)**

Open the downloaded handbook in a browser, or open `docs/index.html` from a local checkout. It embeds the playable game, exploded CAD, circuit traces, software and test records, assembly routing, searchable BOM and interactive cost model. The wiki provides permanent links into the versioned engineering sources. The historical Rev F [engineering release](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/rev-f-engineering-0.7) includes the evidence bundle for offline use.

**Next inert print · TW-A-0001-R0011.** Install the housing receiver-down, with both dovetail lips and the closed end resting on the first layer. Print the service cover and use both maximum-pack gauges. Measure receiver strength and check slide fit on the first article. [Download the private print kit](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/r0011-receiver-fit-print) · [Print and support-removal instructions](hardware/mechanical/TW-A-0001-R0011/PRINT-GUIDE.md)

Personal product project of GitHub user natthapolvanasrivilai. The handheld uses the top-left power key and screw-locked rod grip. It uses the Waveshare capacitive touchscreen controller module. Production disposition is HOLD for physical verification, supplier documentation and market classification.

| Stage | Working record |
|---|---|
| Hardware configuration | [Numeric assembly and part revision register](hardware/revisions/README.md) · [Hardware qualification and first-article status](quality/hardware-gate.md) |
| Product definition | [Requirements and status](product/requirements.md) |
| Industrial design and fit | [R0009 assembled and exploded CAD](docs/models/TW-A-0001-R0009-exploded.html) · [Verification evidence](hardware/mechanical/TW-A-0001-R0009/QA/README.md) |
| Current mechanical candidate | [R0011 receiver toolpaths](hardware/mechanical/TW-A-0001-R0011/README.md) · [Lower service cover and fitted STEP](hardware/mechanical/TW-A-0001-R0010/README.md) |
| Parts and procurement | [Full prototype BOM](sourcing/production-intent/R0009-prototype-budget.csv) · [Exact sources](sourcing/production-intent/R0009-source-evidence.csv) · [Cable routes and connections](hardware/electronics/harness-r0003/README.md) |
| Firmware and game content | [Arduino sketch](firmware/WillowCreek) and [browser game](game/Thai-Waters-play.html) |
| Phone testing | [Private hosted game, QR and motion controls](game/sites/Phone-playtest.md) |
| Verification | [Prototype evidence](verification/fit-review.md) and [bench procedure](verification/bench-guide.md) |
| Market access | [Design and certification review](compliance/market-access.md) |
| Assembly and test | [Build traveler](manufacturing/build-traveler.csv) |
| Pilot, release and service | [Lifecycle gates](manufacturing/gates.md), [release index](releases/README.md), [service](service/README.md) |
| Revisions and third-party rights | [Change register](quality/changes.csv) and [provenance](third-party/NOTICE.md) |
