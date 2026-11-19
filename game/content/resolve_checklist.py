"""Resolve Thai occurrence binomials to accepted GBIF species keys and group synonyms."""
import argparse, concurrent.futures, csv, json, re, time
from pathlib import Path
from urllib.parse import urlencode
import requests

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for key in ("source","output","cache"):ap.add_argument("--"+key,type=Path,required=True)
    args=ap.parse_args()
    rows=list(csv.DictReader(args.source.open(encoding='utf-8')))
    args.cache.mkdir(exist_ok=True,parents=True)
    def resolve(row):
        name=row["scientific_name"]; cache=args.cache/(name+".json")
        if cache.exists(): return json.loads(cache.read_text())
        for attempt in range(6):
            try:
                res=requests.get("https://api.gbif.org/v1/species/match",params={"name":name,"kingdom":"Animalia","phylum":"Chordata"},timeout=35)
                if res.status_code==429:
                    time.sleep(max(10,int(res.headers.get("retry-after","10"))));continue
                res.raise_for_status(); data=res.json()
                if data.get("rank")!="SPECIES" or data.get("matchType")!="EXACT": result=None
                else:
                    key=data.get("acceptedUsageKey") or data["usageKey"]
                    result=(key,data.get("species") or data["canonicalName"],data.get("family") or row["family"],data.get("order") or row["order"])
                cache.write_text(json.dumps(result));return result
            except (OSError,ValueError):
                if attempt==5:raise
                time.sleep(3*(attempt+1))
        raise RuntimeError("GBIF rate limit. Resume using the same cache.")
    accepted={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for row,r in zip(rows,pool.map(resolve,rows)):
            if r and re.fullmatch("[A-Z][a-z]+ [a-z-]+",r[1]):
                key,name,family,order=r
                if key not in accepted or name==row["scientific_name"]:
                    accepted[key]=dict(gbif_key=key,scientific_name=name,family=family,order=order,evidence_name=row["scientific_name"])
    with args.output.open("w",encoding="utf-8",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=["gbif_key","scientific_name","family","order","evidence_name"]);writer.writeheader()
        writer.writerows(sorted(accepted.values(),key=lambda r:r["scientific_name"]))
    print(len(accepted),"accepted species keys")
