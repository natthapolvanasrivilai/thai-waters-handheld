"""Extract the three actual copper networks with KiCad Python, then run ngspice on the installed routes."""
import argparse
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ELEC=HERE.parents[1]/"electronics"
sys.path.insert(0,str(HERE.with_name("r0012")))
BOARDS={"A3":"pcb-haptic-cie-r0002/A3-CIE-R0002.kicad_pcb",
        "A4":"pcb-r0004/harness.kicad_pcb","A5":"usb-entry-r0006/usb-input.kicad_pcb"}

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    command=cli.add_subparsers(dest="action",required=True)
    command.add_parser("copper")
    command.add_parser("replay").add_argument("engine",type=Path)
    options=cli.parse_args()
    if options.action=="copper":
        from extract_copper import copper
        result={name:copper(ELEC/board) for name,board in BOARDS.items()}
        (HERE/"copper.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    else:
        from replay import execute
        execute(options.engine.resolve(),output=HERE,routing_file=ELEC/"harness-r0006/routing.json",
                a3_board=BOARDS["A3"],a5_board=BOARDS["A5"],
                reference_usb_copper=HERE.with_name("r0012")/"copper.json")
