---
name: thai-waters-specimen-art
description: Illustrate or review species-specific fish portraits, silhouettes and catch artwork for Thai Waters.
---

Use the owner's exact [reference plate](../../../game/art-source/plate-2.png). Inspect it alongside the fish at native catch-card size. The transparent original has warm highlights on overlapping scales, individually drawn fin rays, a defined eye and gill cover, and a fine pale edge. Carry the distinctive jaw, fin placement, body depth, tail profile and markings of the named species through pixel reduction. Use an unobstructed side profile for most fish and the anatomically informative view for rays or seahorses.

Assign an individual illustration to each species. Preserve stable catalog IDs and saved catches. A recolored family frame or randomized geometric outline fails this requirement even if its pixel hash is unique. Use the same illustration for the catch reveal and journal. Derive the anonymous undiscovered silhouette from its alpha channel.

Use the [field plate manifest](../../../game/art-source/field/plates.json) to bind each cell to its stable species ID. Rebuild with the [field plate compiler](../../../game/art-source/compile-field.cjs), which shares the original palette reduction and outline logic with the [sprite compiler](../../../game/art-source/compile.cjs). Compare the compiled RGB565 sprite with the reference. Check transparent gutters, whiskers, fin tips, snouts and outlines on light and dark water at actual display size. Review congeners together. Record source, species mapping and any outstanding review so future releases can distinguish illustrated entries from unfinished artwork.
