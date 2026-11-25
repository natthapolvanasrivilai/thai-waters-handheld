---
name: thai-waters-handheld-ui
description: Design and test the Thai Waters touchscreen, fishing HUD, paged overlays, catch journal and mobile simulator.
---

Design against the 480 × 320 landscape framebuffer. Thai is the default language. Check Thai vowel and tone marks as well as English at game resolution. Use the established reading face for small labels and the existing location-specific display faces for signage.

Keep fishing visible behind menus. The collection is the full-screen exception. Fit each settings group on one screen with finger-sized targets. Use discrete pages for the species grid and other long selection lists. Use a native two-axis scrollable table with readable sticky headers for per-species catch receipts. Gestures starting inside the table must not turn the species page. Neither a count/recorded best nor a habitat hint supplies missing legacy trip details. The fish grid keeps eight cards on the full 480 × 320 LCD in portrait and landscape; horizontal swipes and pager arrows move one bounded page. Play one short Effects-volume cue only on a successful grid page turn, not on detail swipes, searching or screen entry. Keep Find and filter controls in their own explicit sheet with focus return. Retain selection and page on detail return. Verify the first, middle and last pages, including long labels, in the final Thai and English 480 × 320 canvas after fonts are ready. Keep the responsive phone screenshot and 44 CSS px touch gate separate from raw framebuffer and physical-panel evidence. Use the touch dimensions in [immersive.css](../../../game/src/immersive.css).

Tap water to aim and cast. Place tackle icons in the transparent HUD and line tension at the moving end of the line. During a fight, show line movement and splashes. Reveal the fish on landing, place fish at left and data at right, and let the player tap to continue before filing. Preserve anonymous silhouettes until discovery.

For Daily Cup, lead with the existing target portrait and the qualifying minimum for its actual measurement type, separate from the recorded catch or personal best. Render the calibrated scale on the native LCD and keep “equip and travel” separate from competition entry. Verify touch fit, same-water equip without travel, skip, persistent tackle and the active-cast and unfiled-catch guards in the [tournament check](../../../verification/browser-tests/tournament.cjs).

Exercise changes in the flat LCD and projected device view. Start from the existing [browser checks](../../../verification/browser-tests/package.json) and the [game handbook](../../../docs/wiki/Game-and-demo.md).

For chart pins with overlapping touch areas, show the named choices without moving the player or enabling stale Travel. An exact marker remains direct; a choice only selects. Keep dismissal and focus return clear, and verify Thai/English labels and touch targets with [the browser map check](../../../verification/browser-tests/location-map.cjs).
