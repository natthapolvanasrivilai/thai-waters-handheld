"""Build-time, offline validation of the independently sourced subset of map points."""
import json
import math
from urllib.parse import urlsplit

def inside(point, ring):
    x, y = point
    return sum((v[1] > y) != (u[1] > y) and
               x < (u[0] - v[0]) * (y - v[1]) / (u[1] - v[1]) + v[0]
               for u, v in zip(ring, ring[1:])) % 2 == 1

def load_map(root, locations):
    path = root / "content"
    pilot = json.loads((path / "map-pilot.geojson").read_text(encoding="utf-8"))
    outline = json.loads((path / "map-thailand-outline.json").read_text(encoding="utf-8"))
    assert pilot["type"] == "FeatureCollection" and pilot["schemaVersion"] == 1 and "crs" not in pilot
    assert outline and all(len(r) >= 4 and r[0] == r[-1] for r in outline)
    def coordinate(p):
        return (len(p) == 2 and all(type(v) in (int, float) and math.isfinite(v) for v in p)
                and 97 <= p[0] <= 106 and 5 <= p[1] <= 21)
    assert all(coordinate(p) for ring in outline for p in ring)
    assert len(pilot["label"]) == 2 and all(pilot["label"][k] for k in ("en", "th"))
    ids = {r["id"] for r in locations}
    assert len(ids) == len(locations)
    assert "not a fishing-access point" in pilot["label"]["en"] and "ไม่ใช่จุดเข้าตกปลา" in pilot["label"]["th"]
    sources = pilot["sources"]
    # These are source records and independently identified waterbodies, not routing pins.
    offset = {0:"Mae Ngat Reservoir",2:"Cheow Lan Lake",16:"Kwan Phayao",31:"Ubol Ratana Reservoir",
              19:"Nam Un Reservoir",30:"Chulabhorn Reservoir",32:"Lam Pao Reservoir",
              46:"Sirindhorn Reservoir",56:"Bhumibol Reservoir",70:"Sirikit Reservoir",
              86:"Srinagarind Reservoir",95:"Bang Lang Reservoir"}
    by_id = {row["id"]: row for row in locations}
    seen = set()
    pins = []
    for f in pilot["features"]:
        key = f["id"]
        point = f["geometry"]["coordinates"]
        assert type(key) is int and key not in seen and key in ids and by_id[key]["name"] == offset.get(key)
        assert f["type"] == "Feature" and f["geometry"]["type"] == "Point" and coordinate(point)
        assert all(round(x, 3) == x for x in point) and any(inside(point, r) for r in outline)
        evidence = f["properties"]
        assert evidence["kind"] in {"representative-waterbody-area", "representative-reservoir-area"}
        assert evidence["sourceRow"] and all(
            urlsplit(sources[evidence[k]]["url"]).scheme == "https"
            for k in ("coordinateSource", "identitySource"))
        assert sources[evidence["identitySource"]]["role"] in {"identity-only", "identity-and-extent"}
        if key == 16:
            assert point == [99.875, 19.171] and evidence["sourceRow"] == "540205"
        pins.append([key,*point])
        seen.add(key)
    assert pins and {p[0] for p in pins} == set(offset)
    return {"pins":pins,"outline":outline,"label":pilot["label"]}

def pack(root, locations):
    literal = json.dumps(load_map(root, locations), ensure_ascii=False, separators=(",",":"))
    assert "</script" not in literal.lower()
    model = (root / "src/location-map-model.js").read_text(encoding="utf-8")
    view = (root / "src/location-map.js").read_text(encoding="utf-8")
    assert view.count("@@MAP_BUNDLE@@") == 1
    return model + "\n" + view.replace("@@MAP_BUNDLE@@", literal)


def credits(root):
    """Portable provenance preserved by the standalone offline HTML build."""
    pilot = json.loads((root / "content/map-pilot.geojson").read_text(encoding="utf-8"))
    citation = {
        "title": "Pocket Reel representative waterbody pilot",
        "uses": "Representative waterbody areas only; not access points or routes.",
        "mapSources": {
            **pilot["sources"],
            "natural-earth": {
                "title": "Natural Earth Admin 0 Countries 1:110m, layer 5.1.1",
                "url": "https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/",
                "rights": "Public domain",
                "rightsUrl": "https://www.naturalearthdata.com/about/",
                "changes": "Selected the Thailand record, reused its coarse WGS84 outline."
            }
        },
        "featureSources": [{"gameId": f["id"], **f["properties"]} for f in pilot["features"]],
    }
    dataset = citation["mapSources"]["msea-res-s1"]
    dataset.update({
        "creator": ["S. S. Mahto", "S. Fatichi", "S. Galelli"],
        "copyright": "© Authors 2025",
        "identifier": "https://doi.org/10.5194/essd-17-2693-2025",
        "changes": "Selected eleven reservoir records, rounded WGS84 coordinates to 0.001°, and linked them to stable game IDs."
    })
    citation["mapSources"]["nga-gns-kwan-phayao"]["credit"] = (
        "Geographic Names Database data, names approved by the U.S. Board on Geographic Names and maintained by NGA."
    )
    literal = json.dumps(citation, ensure_ascii=False, separators=(",", ":"))
    assert "</script" not in literal.lower()
    return literal
