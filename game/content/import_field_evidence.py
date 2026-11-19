"""Find additional fish through attributable, country-coded GBIF field records."""
import argparse
import csv
import json
import io
import hashlib
import zipfile
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
API = "https://api.gbif.org/v1/"
INAT = "50c9509d-22c7-4a22-a47d-8c48425ef4a7"
LICENSES = {"https://creativecommons.org/publicdomain/zero/1.0/legalcode": "CC0-1.0",
            "https://creativecommons.org/licenses/by/4.0/legalcode": "CC-BY-4.0"}
FILTERS = dict(country="TH", occurrenceStatus="PRESENT", basisOfRecord=["PRESERVED_SPECIMEN", "HUMAN_OBSERVATION"],
               license=["CC0_1_0", "CC_BY_4_0"])
FIELD = re.compile(r"\b(rearing ponds?|reared|fishing (?:port|pier)|fish landing|landing site|aquari(?:um|a)|captive|cultivated|pet\s+(?:shop|trade)|market|dealer|bought|purchased|"
                   r"trade|imported|hatchery|fish\s*farm|aquaculture|zoo|type locality unknown)\b", re.I)
# Precise map positions and images stay in the source records. Credit follows each occurrence.
THAI_LOCALITY = re.compile(r"\b(gulf (?:of )?(?:thailand|siam)|thai(?:land)?|siam|phuket|krabi|chiang|"
                           r"songkhla|trang|ranong|bangkok|pattani|chon\s?buri|chanthaburi|rayong|satun|"
                           r"phang.?nga|trat|surat|nakhon|nong khai|ko[h]? chang|chao phraya|prachuap)\b",re.I)
BAD_ISSUES = {"COUNTRY_INVALID", "COUNTRY_COORDINATE_MISMATCH", "CONTINENT_COORDINATE_MISMATCH",
              "ZERO_COORDINATE", "COORDINATE_INVALID", "TAXON_MATCH_HIGHERRANK", "TAXON_MATCH_FUZZY",
              "TAXON_MATCH_NONE", "PRESUMED_NEGATED_LATITUDE", "PRESUMED_NEGATED_LONGITUDE"}
# Published national aquaculture introductions, known out-of-range identifications,
# and the existing tinfoil barb's alternate spelling. Sources are in field-evidence.md.
REVIEWED_OUT = {"Cirrhinus cirrhosus", "Ctenopharyngodon idella", "Gibelion catla", "Barbonymus schwanefeldii",
                "Conger conger", "Gymnothorax unicolor", "Epinephelus summana"}
# A collection explicitly covering the Mexican Pacific supplied erroneous Thailand tags.
MEXICAN_PACIFIC = "80bd1db2-f762-11e1-a439-00145eb45e9a"
LOCAL = threading.local()


def checklist_names(path, sha256):
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
        raise ValueError("Unexpected checklist version: " + str(path))
    with zipfile.ZipFile(path) as archive:
        with archive.open("taxon.txt") as raw:
            taxa = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"), delimiter="\t")
            names = set()
            for row in taxa:
                for field in ("scientificName", "acceptedNameUsage"):
                    m = re.match(r"^([A-Z][a-z]+ [a-z][a-z-]+)\b", row.get(field, ""))
                    if m: names.add(m[1])
            return names


def get(url, query=None):
    if not hasattr(LOCAL, "http"):
        LOCAL.http = requests.Session()
        LOCAL.http.headers.update({"User-Agent": "ThaiWaters/verified-field-records"})
    for attempt in range(6):
        try:
            response = LOCAL.http.get(API + url, params=query, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            if attempt == 5:
                raise
            delay = exc.response.headers.get("Retry-After") if exc.response is not None else None
            time.sleep(int(delay) if delay and delay.isdigit() else 2 ** attempt)


def cache(path, retrieve):
    if path.exists():
        return json.loads(path.read_text(encoding="utf8"))
    data = retrieve()
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
    temp.replace(path)
    return data


def order_facets(name):
    matched = get("species/match", dict(name=name, kingdom="Animalia", rank="ORDER"))
    if matched.get("rank") != "ORDER" or matched.get("matchType") != "EXACT":
        raise ValueError("Unresolved fish order " + name)
    totals = {}
    while True:
        rows = get("occurrence/search", FILTERS | dict(orderKey=matched["usageKey"], facet="speciesKey",
                   facetLimit=500, facetOffset=len(totals), limit=0))["facets"][0]["counts"]
        if any(r["name"] in totals for r in rows):
            raise ValueError("repeated species facet page for " + name)
        totals.update({r["name"]: r["count"] for r in rows})
        if len(rows) < 500:
            return totals


def neighboring_records(keys):
    # CC0 evidence used to corroborate a regional range. Each playable taxon also
    # requires its own Thailand specimen or independent photo observations.
    grouped = [keys[i:i + 40] for i in range(0, len(keys), 40)]
    def search(group):
        q = FILTERS | dict(country=["MM", "KH", "LA", "MY", "SG", "VN", "ID"], license="CC0_1_0",
                           hasGeospatialIssue="false", speciesKey=group, facet="speciesKey", facetLimit=100, limit=0)
        return {r["name"]: r["count"] for r in get("occurrence/search", q)["facets"][0]["counts"]}
    totals = {}
    with ThreadPoolExecutor(max_workers=5) as workers:
        for group in workers.map(search, grouped):
            totals.update(group)
    return totals


def store_occurrences(keys, directory):
    by_key = {k: [] for k in keys}
    offset = 0
    while True:
        result = get("occurrence/search", FILTERS | dict(speciesKey=keys, offset=offset, limit=150))
        for record in result["results"]:
            by_key[str(record["speciesKey"])].append(record)
        if result["endOfRecords"]:
            break
        offset += len(result["results"])
    for k, rows in by_key.items():
        cache(directory / ("record-" + k + ".json"), lambda: rows)


def qualifying(record, key, orders):
    r = record
    licence = r.get("license", "").replace("http://", "https://")
    if (str(r.get("speciesKey")) != key or r.get("countryCode") != "TH" or licence not in LICENSES
            or r.get("order") not in orders or r.get("taxonRank") != "SPECIES"
            or str(r.get("acceptedTaxonKey")) != key or not r.get("family")
            or not re.fullmatch(r"[A-Z][a-z]+ [a-z][a-z-]+", r.get("species", ""))
            or r.get("occurrenceStatus") not in ("PRESENT", "DETECTED")
            or BAD_ISSUES.intersection(r.get("issues", [])) or r.get("identificationQualifier")
            or str(r.get("establishmentMeans") or "").lower() in ("captive", "cultivated", "introduced", "invasive")
            or str(r.get("degreeOfEstablishment") or "").lower() in ("captive", "cultivated")):
        return False
    locality = " ".join(str(r.get(k, "")) for k in ("locality", "verbatimLocality", "waterBody", "stateProvince"))
    context = locality + " " + " ".join(str(r.get(k, "")) for k in ("occurrenceRemarks", "habitat", "fieldNotes"))
    if r.get("datasetKey") == MEXICAN_PACIFIC or r.get("family") in ("Cichlidae", "Poeciliidae"):
        return False
    if FIELD.search(context) or not r.get("datasetKey") or not r.get("key"):
        return False
    lat, lon = r.get("decimalLatitude"), r.get("decimalLongitude")
    if lat is not None and lon is not None:
        # Includes nearshore Thai waters; the recorded country must independently match.
        if not (5.25 <= lat <= 20.65 and 96.5 <= lon <= 106.25):
            return False
    elif not THAI_LOCALITY.search(locality):
        return False
    if r["basisOfRecord"] == "PRESERVED_SPECIMEN":
        return bool(r.get("institutionCode") and r.get("catalogNumber"))
    return (r["basisOfRecord"] == "HUMAN_OBSERVATION" and r["datasetKey"] == INAT and lat is not None
            and bool(r.get("eventDate") and r.get("recordedBy"))
            and any(m.get("type") == "StillImage" for m in r.get("media", [])))


def choose(records, regional):
    records = sorted(records, key=lambda r: (r.get("taxonomicStatus") != "ACCEPTED", r.get("decimalLatitude") is None, int(r["key"])))
    for r in records:
        if r["basisOfRecord"] != "PRESERVED_SPECIMEN":
            continue
        types = " ".join(r.get("typeStatus", [])) if isinstance(r.get("typeStatus"), list) else str(r.get("typeStatus") or "")
        if regional or re.search(r"\b(?:holo|para|lecto|syn)type\b", types, re.I):
            return [r]
        for s in records:
            if (s["basisOfRecord"] == "PRESERVED_SPECIMEN" and s["institutionCode"] != r["institutionCode"]
                    and s["datasetKey"] != r["datasetKey"] and r.get("eventDate") and s.get("eventDate")
                    and s["eventDate"][:10] != r["eventDate"][:10]):
                return [r, s]
    if not regional:
        return []
    # One photographed encounter or re-shares of one individual's observation are insufficient.
    records = [r for r in records if r["basisOfRecord"] == "HUMAN_OBSERVATION"]
    for i, r in enumerate(records):
        for s in records[i + 1:]:
            if r["eventDate"][:10] != s["eventDate"][:10] and r["recordedBy"] != s["recordedBy"]:
                return [r, s]
    return []


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--asean", type=Path, required=True)
    parser.add_argument("--griis", type=Path, required=True)
    args = parser.parse_args()
    regional = checklist_names(args.asean, "ede758ac4a292522c4df963fb33efce50c3740f69cb482b4c6de66df30da83ab")
    excluded = checklist_names(args.griis, "785787c97b60d8ba3e20d77c11fbb220a7105013ce8431ca960d596294458557") | REVIEWED_OUT
    directory = args.cache
    directory.mkdir(exist_ok=True, parents=True)
    from expand_atlas import legacy_names, aliases
    with (HERE / "thai-accepted.csv").open(encoding="utf8") as stream:
        base = list(csv.DictReader(stream))
    orders = sorted({r["order"] for r in base})
    seen = {r["scientific_name"] for r in base} | set(legacy_names) | aliases
    old_keys = {r["gbif_key"] for r in base}
    with ThreadPoolExecutor(max_workers=6) as pool:
        candidates = {}
        for rows in pool.map(lambda name: cache(directory / (name + ".json"), lambda: order_facets(name)), orders):
            candidates.update({k: n for k, n in rows.items() if k not in old_keys})
        groups, group, count = [], [], 0
        for k, n in sorted(candidates.items()):
            if (directory / ("record-" + k + ".json")).exists():
                continue
            if group and (len(group) >= 20 or count + n > 125):
                groups.append(group)
                group, count = [], 0
            group.append(k)
            count += n
        if group:
            groups.append(group)
        list(pool.map(lambda keys: store_occurrences(keys, directory), groups))
        nearby = cache(directory / "neighbors.json", lambda: neighboring_records(sorted(candidates)))
        records, datasets = [], set()
        for key in sorted(candidates):
            raw = json.loads((directory / ("record-" + key + ".json")).read_text(encoding="utf8"))
            eligible = [r for r in raw if qualifying(r, key, orders) and r["species"] not in excluded]
            if not eligible: continue
            in_region = eligible[0]["species"] in regional
            witnesses = choose(eligible, in_region and nearby.get(key,0) >= 2)
            if not witnesses or witnesses[0]["species"] in seen:
                continue
            r = witnesses[0]
            seen.add(r["species"])
            datasets.update(x["datasetKey"] for x in witnesses)
            records.append(dict(gbif_key=key, scientific_name=r["species"], family=r["family"], order=r["order"],
                                evidence_type=r["basisOfRecord"], asean_match="yes" if in_region else "", nearby_cc0_count=nearby.get(key,0), occurrence_ids="|".join(str(x["key"]) for x in witnesses),
                                dataset_keys="|".join(x["datasetKey"] for x in witnesses),
                                licenses="|".join(LICENSES[x["license"].replace("http://","https://")] for x in witnesses),
                                attribution="|".join((x.get("rightsHolder") or x.get("recordedBy") or x.get("institutionCode") or "") for x in witnesses)))
        def attribution(key):
            d = cache(directory / ("dataset-" + key + ".json"), lambda: get("dataset/" + key))
            return dict(dataset_key=key, title=d["title"], doi=d.get("doi",""), publisher_key=d["publishingOrganizationKey"],
                        citation=(d.get("citation") or {}).get("text",""))
        sources = list(pool.map(attribution, sorted(datasets)))
    records.sort(key=lambda r:r["scientific_name"])
    write_csv(HERE / "thai-field-evidence.csv", records, list(records[0]))
    write_csv(HERE / "thai-field-datasets.csv", sources, list(sources[0]))
    print(len(candidates), "candidate species,", len(records), "qualifying new species,", len(sources), "attributed datasets")


if __name__ == "__main__":
    main()
