"""Refresh country-occurrence evidence for fish families in the ASEAN fish checklist."""
import argparse, concurrent.futures, csv, io, json, re, time, zipfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ARCHIVE = "https://ipt.aseanbiodiversity.org/archive.do?r=aseanfishspecieslist&v=7.13"
API = "https://api.gbif.org/v1/occurrence/search"
def fetch(url):
    for attempt in range(4):
        try:
            with urlopen(Request(url,headers={"User-Agent":"ThaiWatersChecklist/1.0"}), timeout=45) as f:
                return f.read()
        except OSError:
            if attempt == 3: raise
            time.sleep(10 * 2 ** attempt)
def collect(args):
    if not args.archive.exists(): args.archive.write_bytes(fetch(ARCHIVE))
    with zipfile.ZipFile(args.archive) as z:
        taxa = list(csv.DictReader(io.TextIOWrapper(z.open("taxon.txt"),encoding="utf-8-sig"),delimiter="\t"))
    families = sorted({t["family"] for t in taxa if t["family"]})
    args.cache.mkdir(parents=True, exist_ok=True)
    def one_family(family):
        path = args.cache / (family+".json")
        if path.exists(): return json.loads(path.read_text())
        q = dict(country="TH", scientificName=family, occurrenceStatus="PRESENT",
                 license="CC0_1_0", facet="scientificName", facetLimit=1000, limit=0)
        result=json.loads(fetch(API+"?"+urlencode(q)))
        counts=result["facets"][0]["counts"] if result["facets"] else []
        if len(counts)>=1000: raise ValueError("uncaptured records in "+family)
        names=[r["name"] for r in counts]
        path.write_text(json.dumps(names))
        return names
    rows={}
    actual={r["scientificName"]:(r["family"],r["order"]) for r in taxa}
    family_order={r["family"]:r["order"] for r in taxa}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for fam,names in zip(families,pool.map(one_family,families)):
            for full in names:
                m=re.match(r"^([A-Z][a-z]+ [a-z][a-z-]+)(?:,?\s|$)", full)
                if not m: continue
                name=m[1]
                if name.split()[1] in ("sp","spp","cf","aff","species"): continue
                # Store the Thai occurrence and flag a second independent regional match.
                if name in actual and actual[name][0] != fam: continue
                rows[name]=(fam,family_order[fam],"ASEAN + GBIF" if name in actual else "GBIF occurrence")
    with args.output.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["scientific_name","family","order","evidence"])
        w.writerows((name,*rows[name]) for name in sorted(rows))
    print(f"{len(rows)} matched species in {len(families)} family queries")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for param in ("archive","cache","output"):p.add_argument("--"+param,type=Path,required=True)
    collect(p.parse_args())
