"""Reconcile printed national checklist entries to exact accepted fish keys, preserving IDs."""
import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import threading
import time
import zipfile
import requests

HERE=Path(__file__).resolve().parent
PDF_SHA="5aae8925cf83ae199759ccc8c21c6b7db6968898a639086c77ec93d76f4e3a28"
API="https://api.gbif.org/v1/species/match"
BINOMIAL=re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+$")
INDEX_ROW=re.compile(r"^([A-Z][a-z]+)\s+(?:\(([A-Z][a-z]+)\)\s+)?([a-zA-Z][a-z-]+)\b.*?(\d{1,3})\s*$")
local=threading.local()


def extract(text):
    pages=text.split("\f");body={};names={}
    for page in pages:
        header=re.search(r"Order/Family Genus/Species Locality Reported by/Year\s+(\d+)",page)
        if header:
            body[int(header[1])]=page
        if not page.startswith("SPECIES INDEX"):
            continue
        for line in page.splitlines():
            line=line.strip()
            if line.startswith("Clupea Amblygaster sirm "):
                line=line.replace("Clupea Amblygaster","Clupea (Amblygaster)",1)
            if line.startswith("Cyclocheilichthys Mae Klongensis "):
                line=line.replace("Mae Klongensis","maeklongensis",1)
            m=INDEX_ROW.match(line)
            if not m or m[3].lower() in ("sp","spp","cf","aff"):
                continue
            name=m[1]+" "+m[3].lower()
            names.setdefault(name,set()).add(int(m[4]))
    # An index may cross-reference a synonym. Accept an explicit binomial or the
    # same genus initial and epithet in the referenced country table, then obtain
    # the current key from GBIF. Absent table evidence stays in the audit ledger.
    out={}
    for name,refs in names.items():
        genus,epithet=name.split()
        field=rf"(?:\b{genus}\b|\b{genus[0]}\.)\s+(?:\([A-Za-z]+\)\s+|Amblygaster\s+)?{epithet}\b"
        valid=[p for p in sorted(refs) if re.search(field,body.get(p,""),flags=re.I)]
        if not valid:
            # Some printed references are off by a page. Search full genus only
            # outside the cited page to avoid assigning the wrong abbreviated genus.
            full=rf"\b{genus}\s+(?:\([A-Za-z]+\)\s+)?{epithet}\b"
            valid=[p for p,t in body.items() if re.search(full,t,re.I)]
        out[name]=(sorted(refs),sorted(set(valid)))
    return out


def primary_table(pdf):
    """Read the italic name at the main row's left margin in the species column."""
    from pypdf import PdfReader
    out={};last=""
    for page in PdfReader(str(pdf)).pages[24:296]:
        fragments=[]
        def visit(txt,cm,tm,font,size):
            x=tm[4]*cm[0]+tm[5]*cm[2]+cm[4]
            if (txt.strip() and font and "Italic" in str(font.get("/BaseFont","")) and
                abs(x-144.6)<=1.1 and 8.5<=tm[0]<=9.5):
                fragments.append(txt.strip())
        page_text=page.extract_text(visitor_text=visit)
        header=re.search(r"Order/Family Genus/Species Locality Reported by/Year\s+(\d+)",page_text)
        if not header:continue
        page_no=int(header[1])
        for line in fragments:
            # Never promote an indented synonym, genus-only entry, or misidentification note.
            m=re.match(r"^([A-Z][a-z]+|[A-Z]\.)\s*(?:\([A-Za-z.]+\)\s*)?([a-zA-Z][a-z-]+)\b",line)
            if not m:continue
            genus,epithet=m[1],m[2].lower()
            if genus.endswith("."):
                if genus[0]!=last[:1]:continue
                genus=last
            else:
                # Require a separator after the full genus (the regex can backtrack
                # into a one-word entry). A full name sets the continuation genus.
                if not line.startswith(genus+" ") and not line.startswith(genus+"("):continue
                last=genus
            if epithet in ("sp","spp","cf","aff"):continue
            out.setdefault(genus+" "+epithet,set()).add(page_no)
    return out


def resolve(name,cache):
    path=cache/(name+".json")
    if path.exists():
        d=json.loads(path.read_text(encoding="utf8"))
        return d.get("accepted") if isinstance(d,dict) else d
    if not hasattr(local,"http"):
        local.http=requests.Session()
        local.http.headers["User-Agent"]="ThaiWatersChecklist/1.0 (taxonomic checklist reconciliation)"
    for attempt in range(6):
        try:
            resp=local.http.get(API,params={"name":name,"kingdom":"Animalia","phylum":"Chordata"},timeout=25)
            if resp.status_code==429:
                time.sleep(max(15,int(resp.headers.get("Retry-After",15))));continue
            resp.raise_for_status();d=resp.json()
            # Exact synonyms have a separate acceptedUsageKey; species and
            # speciesKey describe the accepted entity, canonicalName the synonym.
            result=None
            if (d.get("matchType")=="EXACT" and d.get("rank")=="SPECIES" and
                d.get("kingdom")=="Animalia" and d.get("phylum")=="Chordata" and
                d.get("status") in ("ACCEPTED","SYNONYM") and d.get("family") and
                d.get("order") and (d.get("canonicalName") or "").lower()==name.lower()):
                key=d.get("acceptedUsageKey") or d["usageKey"]
                scientific=d.get("species") or d["canonicalName"]
                if BINOMIAL.fullmatch(scientific) and d.get("speciesKey",key)==key:
                    result=[key,scientific,d["family"],d["order"]]
            path.write_text(json.dumps(result),encoding="utf8")
            return result
        except (requests.RequestException,ValueError):
            if attempt==5:raise
            time.sleep(2**attempt)
    raise RuntimeError("GBIF throttled; resume with the same cache")


def write(path,rows,fields):
    with path.open("w",encoding="utf8",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def main():
    p=argparse.ArgumentParser()
    for name in ("pdf","archive","cache","base","output","audit"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--text",type=Path,help="Existing pypdf pages joined with form feeds")
    args=p.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest()!=PDF_SHA:
        raise ValueError("Expected the May 1997 OEPP national checklist")
    if args.text:
        text=args.text.read_text(encoding="utf8")
    else:
        from pypdf import PdfReader
        text="\f".join(x.extract_text() or "" for x in PdfReader(str(args.pdf)).pages)
    names=extract(text)
    primary=primary_table(args.pdf)
    for name,pages in primary.items():
        refs,valid=names.get(name,([],[]))
        names[name]=(refs,sorted(set(valid)|pages))
    print("Candidate names",len(names),"primary table names",len(primary),"names found in table text",sum(bool(r[1]) for r in names.values()),flush=True)
    with zipfile.ZipFile(args.archive) as z:
        reader=csv.DictReader(io.TextIOWrapper(z.open("taxon.txt"),encoding="utf-8-sig"),delimiter="\t")
        asean={r["scientificName"] for r in reader}
    with args.base.open(encoding="utf8") as source:
        original=list(csv.DictReader(source))
    occurrences={r["scientific_name"]:r["evidence"] for r in csv.DictReader((HERE/"thai-occurrence.csv").open(encoding="utf8"))}
    records={}
    for r in original:
        if r.get("evidence_sources") and "TH occurrence" not in r["evidence_sources"]:
            continue
        key=int(r["gbif_key"]);sources=["GBIF TH occurrence"]
        if "ASEAN" in occurrences.get(r["evidence_name"],""):
            sources.append("ASEAN v7.13")
        records[key]={k:r[k] for k in ("gbif_key","scientific_name","family","order","evidence_name")}
        records[key].update(evidence_sources="; ".join(sources),oepp_name="",oepp_page="")
    args.cache.mkdir(exist_ok=True,parents=True)
    # Use the accepted key for the hand-authored core as well. Its names are
    # identifiers in the existing generator and are never mutated here.
    import expand_atlas
    lookup=sorted({k for k,v in names.items() if v[1]} | set(expand_atlas.legacy_names))
    print("New lookups",sum(not (args.cache/(k+".json")).exists() for k in lookup),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results=dict(zip(lookup,pool.map(lambda n:resolve(n,args.cache),lookup)))
    legacy={results[n][0]:n for n in expand_atlas.legacy_names if results.get(n)}
    ledger=[]
    for name,(index,valid) in sorted(names.items()):
        r=results.get(name) if valid else None
        national=name in primary
        state=("accepted primary row" if national else "index or alternate name only") if r else ("no exact species match" if valid else "table name unconfirmed")
        ledger.append(dict(checklist_name=name,index_refs=";".join(map(str,index)),table_refs=";".join(map(str,valid)),primary_row_pages=";".join(map(str,sorted(primary.get(name,())))),status=state,
                           gbif_key=r[0] if r else "",accepted_name=r[1] if r else "",
                           asean_match="yes" if name in asean or r and r[1] in asean else ""))
        if not r or not national:continue
        key,taxon,family,order=r
        if not BINOMIAL.fullmatch(taxon) or not family or not order:continue
        rec=records.setdefault(key,dict(gbif_key=key,scientific_name=taxon,family=family,order=order,
                    evidence_name=name,evidence_sources="",oepp_name="",oepp_page=""))
        flags=set(filter(None,rec["evidence_sources"].split("; ")))|{"OEPP 1997 national checklist"}
        if name in asean or taxon in asean:flags.add("ASEAN v7.13")
        rec["evidence_sources"]="; ".join(sorted(flags))
        if not rec["oepp_name"] or name==taxon:
            rec["oepp_name"]=name;rec["oepp_page"]=";".join(map(str,sorted(primary[name])))
    fields=["gbif_key","scientific_name","family","order","evidence_name","evidence_sources","oepp_name","oepp_page"]
    write(args.output,sorted(records.values(),key=lambda r:r["scientific_name"]),fields)
    write(args.audit,ledger,list(ledger[0]))
    print("Accepted keys",len(records),"national only",sum("TH occurrence" not in r["evidence_sources"] for r in records.values()))
    print("Legacy canonical alias keys",[(n,records[k]["scientific_name"],k) for k,n in legacy.items()
          if k in records and n!=records[k]["scientific_name"]],flush=True)


if __name__=="__main__":
    main()
