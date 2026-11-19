# LCD species artwork

The built-in ImageGen editor produced these ten transparent plates from the original game palette. The brief called for a whole, right-facing natural-history sprite, species-specific anatomy, fins and markings, and a single cream contour. The collectible ray uses a dorsal view. The eight fictional species have original designs.

The plate order matches the stable 52 original field-guide IDs, followed by the eight fictional species and sixteen additional family illustrations. The expanded checklist points to a representative silhouette through each entry's art field. The original PNG plates remain in the private design source. Only the packed sprites ship on the handheld.

Run `node game/art-source/compile.cjs` from the repository root after installing the existing game/lan dependencies. The compiler samples 96 × 50 pixels per specimen and supplies matching 4-bit indices and 16-color RGB565 palettes to the simulator and handheld. The 76 frames and palettes use 184,832 bytes before compiler alignment. The web journal downsamples each frame for its 48 × 25 thumbnails.
