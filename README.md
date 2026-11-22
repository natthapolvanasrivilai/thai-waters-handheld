# Thai Waters handheld

[Hardware closure and playtest issues](quality/hardware-gate.md) · [Open the private tracker](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/1)

[Private touch playtest](https://thai-waters-pocket-angler.shoung0690.chatgpt.site) · [Builds and verification](docs/wiki/Software-and-tests.md#current-release) · [Clock and collection recovery](docs/wiki/Clock-and-saves.md)

[Hardware revisions and CAD](docs/wiki/Hardware-and-3D.md) · [One-unit BOM and price research](docs/wiki/BOM-and-business.md) · [Current release and hardware milestone](docs/wiki/Software-and-tests.md#current-release)

**[Browse the canonical product wiki](docs/wiki/Home.md)** · **[Download the archived interactive handbook](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0011-hardware-review-1/Thai-Waters-handbook.html)** · **[Play on a phone](https://thai-waters-pocket-angler.shoung0690.chatgpt.site)**

The version-controlled product wiki is the source of truth for product documentation. The archived R0011 interactive handbook and `docs/index.html` are engineering snapshots with an older embedded simulator, exploded CAD, circuit traces and the BOM. Use the private touch playtest for current gameplay; the handbook identifies the exact software build and verification run. The historical Rev F [engineering release](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/rev-f-engineering-0.7) includes the evidence bundle for offline use.

**Archived inert-print procedure · TW-A-0001-R0011.** Install the housing receiver-down, with both dovetail lips and the closed end resting on the first layer. Print the service cover and use both maximum-pack gauges. Measure receiver strength and check slide fit on the first article. [Archived print kit](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/r0011-receiver-toolpaths-2) · [Print and support-removal instructions](hardware/mechanical/TW-A-0001-R0011/PRINT-GUIDE.md)

Personal product project of GitHub user natthapolvanasrivilai. The handheld uses the top-left power key and screw-locked rod grip. It uses the Waveshare capacitive touchscreen controller module. Production disposition is HOLD for physical verification, supplier documentation and market classification.

| Stage | Working record |
|---|---|
| Hardware configuration | [Numeric assembly and part revision register](hardware/revisions/README.md) · [Hardware qualification and first-article status](quality/hardware-gate.md) |
| Product definition | [Requirements and status](product/requirements.md) |
| Industrial design and fit | [R0011 assembly inspection and STEP](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/r0011-hardware-review-1) · [Mechanical verification](hardware/mechanical/TW-A-0001-R0011/README.md) |
| Archived mechanical candidates | [R0011 receiver toolpaths](hardware/mechanical/TW-A-0001-R0011/README.md) · [Lower service cover and fitted STEP](hardware/mechanical/TW-A-0001-R0010/README.md) |
| Parts and procurement | [R0011 / R0004 engineering BOM](sourcing/production-intent/R0011-R0004-BOM.md) · [Line items and source evidence](sourcing/production-intent/R0011-R0004-engineering-BOM.csv) · [Cable routes and connections](hardware/electronics/harness-r0003/README.md) |
| Firmware and game content | [Arduino sketch](firmware/WillowCreek) · [Hosted browser and matching verification record](docs/wiki/Software-and-tests.md#current-release) · [Historical engineering downloads](docs/wiki/Software-and-tests.md#historical-builds) |
| Phone testing | [Private hosted game, QR and motion controls](game/sites/Phone-playtest.md) |
| Verification | [Prototype evidence](verification/fit-review.md) and [bench procedure](verification/bench-guide.md) |
| Market access | [Design and certification review](compliance/market-access.md) |
| Assembly and test | [Build traveler](manufacturing/build-traveler.csv) |
| Pilot, release and service | [Lifecycle gates](manufacturing/gates.md), [release index](releases/README.md), [service](service/README.md) |
| Revisions and third-party rights | [Change register](quality/changes.csv) and [provenance](third-party/NOTICE.md) |
