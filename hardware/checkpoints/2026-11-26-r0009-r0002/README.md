# Pocket Reel hardware checkpoint — 2026-11-26

Engineering hold, not a manufacturing release. HWS-001 Rev 0.3 pairs enclosure TW-A-0003-R0009 and PCB TW-A-0004-R0002. Base: PR #98, commit 9abc5096fec9e24ba23b13151e6d650588ba1d20. The housing, gauge and PCB STEP are included as checkoutable bytes. Existing production and published release selection are unchanged.

Verify from this directory with `sha256sum -c SHA256SUMS`. Run `python3 pcb/step-transform-audit.py` and `python3 pcb/wire-land-audit.py` for the placement and bare-land screens. Run `python3 dfm/inert_insertion_yaw.py` with CadQuery/OCP for the inert gauge check. Read the reports for applicability; nothing here substitutes for native assembly, physical trial or power qualification.

Keep each actual design revision on a durable branch. Keep experiments separate; preserve prior references. Promote to main by reviewed PR only after matching PCB, CAD, firmware and manufacturing evidence passes. Do not order PCB or start final printing until approval and GitHub confirms the repository is private. A future visibility change cannot retract existing public copies.
