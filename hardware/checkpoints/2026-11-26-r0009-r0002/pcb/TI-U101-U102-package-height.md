# R0002 comparator height provenance

Exact R0002 BOM/placement: U101 TLV3011BIDBVR, U102 TLV3011BIDCKR. TI's [TLV3011 family datasheet and package addendum](https://www.ti.com/lit/ds/symlink/tlv3011.pdf) maps those ordering codes to DBV and DCK respectively. Use the mechanical outline height from the package seating plane, not the 35 mm or 18 mm tape/reel shipping dimensions in the same PDF.

| Ref | Exact mechanical outline | Maximum seating-plane height |
|---|---|---:|
| U101 | DBV0006A, 4214840/G, 08/2024 | 1.45 mm |
| U102 | DCK0006A, 4214835/D, 11/2024 | 1.10 mm |

Both package seating-plane origins are Z = 0.795 mm with STEP axis +Z. Thus, using the same nominal origin, the supplier maximum package-only points can extend to Z = 2.245 mm and 1.895 mm respectively in STEP. These are not installed limits. Keep PCB seating/warp, actual package lift and tilt from solder, and placement uncertainty as separate terms. This height-only provenance does not enclose lateral flash/protrusion, leads, solder fillets, or nearby wires and is not a sweep or fit pass. Next: compare true named CAD solid surfaces with a supplier-bounded 3D envelope and witness the installed seating/protrusions.
