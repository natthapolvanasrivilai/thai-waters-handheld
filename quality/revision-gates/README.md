# Pocket Reel revision constitution

This is the release decision record, not an assertion that the current device is ready. Continue ordinary development commits, reviewed PRs, non-promotional engineering checkpoints and existing read-only verification without a production gate. Follow existing owner-private distribution restrictions and the hardware holds. In particular, this policy does not turn a public repository, public CI log, nightly artifact or GitHub prerelease into authorization to disclose private source, hardware, evidence or manufacturing data.

| State | Gate |
|---|---|
| Engineering checkpoint | Clearly mark what changed, exact source, unresolved safety and test gaps. No ready-for-use, production or order claims. Existing build/verification and private nightly controls are unchanged. |
| Deliberate prototype promotion | Pass the appropriate minimum in each included discipline and the non-waivable hazard review. Inert prints also require native printability. Powered prototypes require PCB layout/populated fit, controlled bench limits, measured protective/fault behavior, and fit/service first article. Failure blocks the revision; optional incomplete checks remain pending, not N/A. |
| Production promotion or any production order | All checks pass, full powered product scope, repository verified private, express owner approval in a GitHub review tied to the exact evidence commit and source. Recheck current facts at action time; no purchase or public distribution is implied. |

A software-only prototype cannot contain hardware outputs. Explain why omitted hardware checks do not apply. An inert prototype cannot energize any circuit; it may mark measured active power protection N/A with a rationale, but it cannot omit hazard review. Only designated check IDs allow N/A; production does not. Keep safety limits appropriate to the test, and retain independent human review even when the script passes.

## Minimum evidence and production closeout

- **Mechanical/FDM:** exact CAD, native print project/configuration and material; check overhang supports and removal, weak/thin features, visible surface defects, dimensional/first-article evidence.
- **PCB:** schematic, ERC, exact BOM and footprint provenance; layout DRC, electrical/mechanical keepouts, placements and 3D assembly; physical bring-up with calibrated observations. Identify unresolved component/connector substitutions by exact identity.
- **Power:** written hazards, sources/load and foreseeable misuse, explicit permitted exposure; bench controls, current, charging, temperature and isolation limits; measured fault protection with limits, setup, time, readings and disposition. Record applicable product safety/compliance evidence before full production.
- **Software/firmware:** build source/digests; hardware compatibility, backed-up saves and recovery; target regression, migration, update and rollback; representative end-to-end endurance with the real build.
- **Assembly:** version-matched interfaces, tool access, service instructions and datum sequence; no-force physical fit and repeatable acceptance/QC; evidence for all released accessories.
- **Packaging:** exact configuration, BOM, serial/lot traceability; protection, labels, instructions and compliance; validation for intended transportation/load/region.

## Per-revision workflow

1. Lock the exact source commit (assembly and part revisions, PCB/BOM, firmware and native slices). Copy [the blank manifest](template.json) to a revision-specific filename in this directory. A separate evidence commit follows the source commit. Do not fabricate evidence or record only its intended path.
2. For each check, capture method, acceptance limit, observed result, artifact checksum, date and reviewer in tracked files under `verification/revision-evidence/`. In public prototype scope include only explicitly shareable evidence. A human must determine whether evidence is sufficient; the validator enforces structure and digests, not factual accuracy.
3. Run `python3 tools/revision_gate.py . quality/revision-gates/<revision>.json <exact-evidence-sha>` for local prototype checking. The local command is not reliable proof of production approval. A fixture or locally supplied facts file does not convey owner authorization.
4. Production only: the owner reviews the evidence PR at its **current exact HEAD**; the approving review must include a standalone line `release-gate: production REVISION FULL_SOURCE_SHA`. Use a reviewable PR author distinct from the owner so GitHub allows the owner to approve it. A newer substantiated owner rejection/dismissal, changed head, missing approval or public repository fails this gate. Revise and re-review when evidence or source changes.
5. From the trusted default branch, manually dispatch **Revision release gate**, passing the evidence SHA, the tracked manifest path, and the production review PR if applicable. Verify the successful `check_revision` job, not merely policy unit tests. Do not attach release credentials to the workflow, and do not run code from the evidence checkout.
6. A passing check permits a human to consider promotion. Before a real promotion/order, use the latest result, verify privacy and review have not changed, and obtain separate approval for the action according to its scope. Record exact source, evidence run/commit, approved artifact SHA-256 and production lot/order in a controlled record.

## Technical boundary

The proposed gate does not publish, sign, power, merge, tag, pay, change visibility or create an order. It does not change existing artifact/nightly workflows (the current nightly publisher independently requires private visibility). A repository administrator must adopt it in rulesets/required checks and integrate it into any future production-publish or ordering workflow; direct GitHub releases, manual tagging, alternate workflows and external orders are not technically prevented by this repo-only proposal. GitHub Actions settings/ruleset protection and private visibility must be verified independently before use. The owner’s public engineering/development checkpoint authority is not extended.
