# Offline Thailand map pilot

This is a representative locator for selected waterbodies in the game. A diamond shows an approximate waterbody area, never a fishing spot, entrance, navigation waypoint, regulation, or permission. The original destination list/search remains authoritative for all game destinations; entries without independently verified evidence receive no marker. Coordinates are RFC 7946 WGS84 longitude/latitude, rounded to 0.001° for the country overview. Stable game IDs, not order or fish pools, link the data to destination names.

## Map attribution

The standalone offline HTML includes complete machine-readable attribution in the inert JSON element `mapSources`: creator, source and licensing URLs, per-marker provenance, and modification notices. The visible map credits remain onsite.

- Outline: [Natural Earth Admin 0 Countries, 1:110m, layer 5.1.1](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/), [public domain](https://www.naturalearthdata.com/about/), distributed in the [official v5.1.2 package](https://github.com/nvkelso/natural-earth-vector/tree/v5.1.2/110m_cultural). Extracted THA record with official WGS84 PRJ and serialized one closed 64-point ring. Upstream source Git blobs: SHP `9318e45c7015568100ad4d7a271790fbec966876`, DBF `e0acd0664f4b920d58ea77e572c2af6ea31a1a3c`, PRJ `b13a71791932a9ecb82a81800e49b3d5b307a195`, VERSION `ac14c3dfaa865ea332c62348d1bca867bdbbd1cf`. This coarse overview cannot show all minor islands, detailed shorelines or legal borders.
- Reservoir facts: Mahto, S. S., Fatichi, S., and Galelli, S. (2025), [MSEA-Res](https://essd.copernicus.org/articles/17/2693/2025/), supplementary Table S1, DOI 10.5194/essd-17-2693-2025. © authors, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Adapted by selecting, rounding and joining to stable game IDs. The GeoJSON gives the independent official Thai identity source for each record.
- Kwan Phayao: [official NGA GNS WGS84 record 540205](https://geonames.nga.mil/geon-ags/rest/services/RESEARCH/GIS_OUTPUT/MapServer/0/540205) and linked Thai variant 540204 (same unique feature). [NGA GNS](https://geonames.nga.mil/geonames/GNSHome/index.html) permits use and recommends credit: Geographic Names Database data, names approved by US BGN and maintained by NGA. Thailand's ONEP natural-site profile and northern wetlands record p.46 independently establish the named waterbody and its approximate extent. No third-party imagery, live tiles or descriptions copied.

## Northeast reservoir follow-up

| Existing game destination | Representative longitude, latitude | MSEA-Res Table S1 row | Independent identity |
| --- | --- | --- | --- |
| #19 Nam Un Reservoir (Sakon Nakhon) | 103.747, 17.297 | Nam_Oun | [RID large-reservoir list](https://water.rid.go.th/hydhome/document/2555/order-OWMH.pdf) |
| #30 Chulabhorn Reservoir (Chaiyaphum) | 101.636, 16.539 | Chulabhorn | [EGAT dam background](https://www.egat.co.th/home/en/chulabhorn-dm-about/) |
| #32 Lam Pao Reservoir (Kalasin) | 103.440, 16.654 | Lam_Pao | [RID large-reservoir list](https://water.rid.go.th/hydhome/document/2555/order-OWMH.pdf) |

The nine existing markers are unchanged. The three points are source-record markers, not measured shore positions or permission to fish. Destination names, save IDs and fish pools are unchanged.

Add evidence and exact intended game-ID/name validation before any new marker. Do not batch-fill coordinates with provincial centroids or geocoders that return roads, similarly named villages, or separately sourced access points. Build validation and source-file attribution supplement browser QA; do not publish the map when actual selection, keyboard, drag/tap separation, and explicit travel are unverified.
