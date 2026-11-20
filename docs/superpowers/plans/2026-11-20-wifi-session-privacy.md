# Wi-Fi Session Privacy Implementation Plan

> For engineering: apply TDD, then run fake hooks and target compile before a release proposal.

**Goal:** Preserve the local Phone setup, with session-only Wi-Fi by default and opt-in persistence on confirmed connection.
**Architecture:** Keep the existing Connected.cpp portal and ESP32 RAM-only SDK mode. Separate closing the portal from restoring pre-setup radio. Save only through the approved application store, never use a real connection for this phase.
**Spec:** Private issue #51; on-device scan, Forget UX, Device Info and authenticated cloud QR are separate acceptance phases.

- [ ] Host fake WiFi, HTTP portal and preferences execute exact Connected.cpp with no device or network access. Observe red on unchecked/masked form.
- [ ] Add unchecked remember input and prevent credential reflection or caching; wait for previous connection to drop before starting an attempt; discard secrets on failure/close.
- [ ] Verify no opt-in means no persistent writes and no existing record is removed; explicitly checked and actually connected is the only save path; preserve older records until Forget.
- [ ] Test late successful status, failure, rejected origin/token, old saved record, close/cancel, failed storage and truthful link versus clock.
- [ ] Document limitations: local WPA-protected SoftAP HTTP, never internet pairing; no real radio/firmware/flash actions in the host gate.
