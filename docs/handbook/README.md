# Maintaining current project status

Update [the status record](../wiki/Current-status.md) in the same change as a new revision, owner observation, print kit, release, or changed project gate. Include the review date, identifiers, physical evidence, open checks and next action. Link directly to the underlying records. The reader accepts plain paragraphs, `##` headings and inline Markdown links to files or releases in this GitHub project.

The [handbook download](https://github.com/natthapolvanasrivilai/thai-waters-handheld/releases/download/r0013-pcb-fit-1/Thai-Waters-handbook.html) discovers the current source each time it opens. A single same-repository open PR can serve as the active engineering review. Append the following marker as the last line of that PR's description, outside any code block.

```text
<!-- current-handbook -->
```

Keep the marker on the current review only. When handing work to the next review, move the marker to the new PR and reopen the download to verify the displayed PR and commit. After merging or closing the marked PR, the reader follows the repository's default branch. Merge the status record with the reviewed evidence before closing a superseded review. If two reviews claim current status, the selected source is missing, GitHub limits requests, or the project requires sign-in, the download shows a warning and its saved release record. A signed-in reader can follow the project reviews link on GitHub. The download sends anonymous requests only to GitHub.

Run `python tools/check_current_handbook.py` to verify the live status, its local evidence links, registered assembly IDs and the packaged reader. For a PR, pass `--base BASE_COMMIT` to check the changed evidence records. Run `node verification/browser-tests/handbook-current.cjs` with the browser test dependencies installed to exercise source selection and offline behavior.

Routine record edits reach existing downloads on their next successful open. When releasing a new offline edition or changing [the reader](live-panel.html), run `python tools/check_current_handbook.py --embed RELEASE_TAG`. Attach the resulting [single-file handbook](../index.html) as `Thai-Waters-handbook.html` in that release. Keep the original live download available as a bookmark. The archived tabs carry their original embedded assets.
