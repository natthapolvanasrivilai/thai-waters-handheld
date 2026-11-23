# Maintaining current project status

Update [the status record](../wiki/Current-status.md) in the same change as a new revision, owner observation, print kit, release, or changed project gate. Include the review date, identifiers, physical evidence, open checks and next action. Link directly to the underlying records. The reader accepts plain paragraphs, `##` headings and inline Markdown links to files or releases in this GitHub project.

The [handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/display-gauge-r0002/Thai-Waters-handbook.html) discovers the current source each time it opens. A single same-repository open PR can serve as the active engineering review. Append the following marker as the last line of that PR's description, outside any code block.

```text
<!-- current-handbook -->
```

Keep the marker on the current review only. When handing work to the next review, move the marker to the new PR and reopen the download to verify the displayed PR and commit. After merging or closing the marked PR, the reader follows the repository's default branch. Merge the status record with the reviewed evidence before closing a superseded review. If two reviews claim current status, the selected source is missing, GitHub limits requests, or the project requires sign-in, the download shows a warning and its saved release record. A signed-in reader can follow the project reviews link on GitHub. The download sends anonymous requests only to GitHub.

Run `python tools/check_current_handbook.py` to verify the live status, its local evidence links, registered assembly IDs and the packaged reader. For a PR, pass `--base BASE_COMMIT` to check the changed evidence records. Run `node verification/browser-tests/handbook-current.cjs` with the browser test dependencies installed to exercise source selection and offline behavior.

Routine record edits reach existing downloads on their next successful open. Keep the original live download available as a bookmark.

## Package the offline PCB assembly guide

1. From the repository root, run `npm ci --prefix game/src` and `python docs/handbook/pcb-assembly/build_view.py` to regenerate the [R0014 guide](../models/R0014-PCB-assembly.html), [R0015 guide](../models/R0015-PCB-assembly.html), [R0016 guide](../models/R0016-PCB-assembly.html) and [R0017 guide](../models/R0017-PCB-assembly.html). Then run `python docs/handbook/pcb-assembly/build_r0013_erratum.py` to apply the legacy stop to the original flat-floor kit. See the [viewer builder](pcb-assembly/build_view.py) for source inputs.
2. When releasing a new offline edition or changing [the reader](live-panel.html), run `python tools/check_current_handbook.py --embed RELEASE_TAG`, followed by `python tools/check_current_handbook.py`. The packager stamps the status snapshot and embeds the standalone HTML bytes. The second command compares the embedded panel with its source and the current standalone file.
3. Run `npm ci --ignore-scripts --prefix verification/browser-tests` and `node verification/browser-tests/handbook-current.cjs`. The test opens the local handbook, uses the PCB assembly tab offline, compares its loaded bytes with the standalone file, then exercises archive navigation. Run `node verification/browser-tests/handbook-current.cjs PATH_TO_PREVIOUS_HANDBOOK --legacy` for a pre-assembly live reader. It checks the standalone download link delivered by the current status record.
4. Attach the [single-file handbook](../index.html) as `Thai-Waters-handbook.html` and the current revision-labelled standalone guide; retain working links to earlier guide releases. Link the current download and the archived guides from the [status record](../wiki/Current-status.md). After publication, open the standalone download from an earlier live reader and compare the downloaded files with the packaged originals.
