"""Generate both full local engineering views from the same installed solids and measured W4 trajectory."""
import argparse
from pathlib import Path
from assemble import HERE,PREVIOUS,WIRES,load
from stroke import new_leads
from service_view import make
from viewer import viewer

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("cache","bundle","exports"):
        cli.add_argument(key,type=Path)
    args=cli.parse_args()
    manifest=HERE/"overlay.json"
    make(args.cache,args.bundle,args.exports,revision=HERE,harness=WIRES,overlay=load(manifest),wire_model=new_leads())
    viewer(args.exports,revision=HERE,previous_rev=PREVIOUS,manifest=manifest)
