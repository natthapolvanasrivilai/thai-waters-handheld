"""Re-evaluate every withdrawal station with the installed display and revised W4, A3 and A5."""
import argparse
import importlib.util
from pathlib import Path

from assemble import HERE, WIRES, load
from service_check import run

def new_leads():
    spec=importlib.util.spec_from_file_location("seated_w4", WIRES/"mate.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cache",type=Path)
    args=cli.parse_args()
    run(args.cache,revision=HERE,harness=WIRES,overlay=load(HERE/"overlay.json"),wire_model=new_leads())
