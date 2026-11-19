# Maintaining the interactive product handbook

The front door is [the repository wiki](../../docs/wiki/Home.md). The compiled [offline handbook](../../docs/index.html) has eight bookmarkable views. Append `#assembly`, `#circuits`, `#software`, `#validation`, `#factory`, `#business` or `#demo` to its local URL to share a starting point. Each chapter links to the corresponding source or test file.

## Rebuild a revision

1. Start in the repository root. Extract the [private engineering pack](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/tag/rev-f-engineering-0.7) into a separate export directory. It supplies the standalone exploded viewer, renders, full STEP, frozen print kit and other engineering exports. To regenerate the geometry after a mechanical change, follow the [mechanical build instructions](../../hardware/mechanical/rev-F/review/README.md).
2. Rebuild the [single-file game](../../game/BUILD.md) and its WASM modules after firmware or scenery changes. Update circuit evidence, the sourcing model, software evidence CSV and factory matrix when their source changes. Keep separate rows for simulated results and actual serialized bench measurements.
3. Run the following commands in PowerShell. Substitute your export path. Set `BROWSER_PATH` to the local Chromium executable on systems without Edge. The browser test opens the offline handbook, plays a cast, checks the actual 3D canvas, navigates the software and factory screens, selects simulation cases, tests the BOM controls and exports the print companion.

```powershell
$exports = Resolve-Path ../outputs
python -X utf8 manufacturing/rev-F-review/build_review.py --outputs $exports
Copy-Item "$exports/Riffle-Rev-F-engineering-review.html" docs/index.html
python -X utf8 manufacturing/rev-F-review/check_handbook.py
npm --prefix verification/browser-tests ci
node verification/browser-tests/handbook.cjs $exports
python -X utf8 manufacturing/rev-F-review/package_evidence.py $exports
```

4. Commit the wiki, rendered handbook and engineering records together. Attach the verified archive, offline handbook and print companion to the matching private GitHub release. The archive includes a SHA-256 manifest for each member. The phone playtest has its own owner-only deployment. Commercial and engineering files belong in this private project.

## Evidence ownership

| Change | Update with it |
|---|---|
| New module, battery, mechanical clearance or harness route | CAD part manifest, fit checks, BOM, incoming inspection, assembly station and unit record |
| Circuit value, operating mode or current budget | Solver inputs, raw traces, pass/fail criteria and corresponding bench protocol |
| Firmware behavior or hardware API | Source, normal-entry regression, actual board build, application hash and software evidence row |
| Supplier, process, price or market | BOM assumptions, manufacturing scenario, launch plan and market-access evidence |

The print companion captures the engineering review; the runnable game, selectable geometry and filters are in the HTML.
