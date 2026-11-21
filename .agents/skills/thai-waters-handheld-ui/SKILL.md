---
name: thai-waters-handheld-ui
description: Design and test the Thai Waters touchscreen, fishing HUD, paged overlays, catch journal and mobile simulator.
---

Design against the 480 × 320 landscape framebuffer. Thai is the default language. Check Thai vowel and tone marks as well as English at game resolution. Use the established reading face for small labels and the existing location-specific display faces for signage.

Keep fishing visible behind menus. The collection is the full-screen exception. Fit each settings group on one screen with finger-sized targets. Use discrete pages for long lists and history. The fish grid keeps eight cards on the full 480 × 320 LCD in portrait and landscape; horizontal swipes and pager arrows move one bounded page. Play one short Effects-volume cue only on a successful grid page turn, not on detail swipes, searching or screen entry. Keep Find and filter controls in their own explicit sheet with focus return. Retain selection and page on detail return. Verify the first, middle and last pages, including long labels, in the final Thai and English 480 × 320 canvas after fonts are ready. Keep the responsive phone screenshot and 44 CSS px touch gate separate from raw framebuffer and physical-panel evidence. Use the touch dimensions in [immersive.css](../../../game/src/immersive.css).

Tap water to aim and cast. Place tackle icons in the transparent HUD and line tension at the moving end of the line. During a fight, show line movement and splashes. Reveal the fish on landing, place fish at left and data at right, and let the player tap to continue before filing. Preserve anonymous silhouettes until discovery.

Exercise changes in the flat LCD and projected device view. Start from the existing [browser checks](../../../verification/browser-tests/package.json) and the [game handbook](../../../docs/wiki/Game-and-demo.md).
