"""Rebuild the handheld game's standalone browser engine with Zig 0.13.x."""
from catch_weights import write_catch_weights

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--zig", default="zig", help="Zig executable or path")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
assets = root / "game" / "assets"
write_catch_weights()
with tempfile.TemporaryDirectory(dir=assets) as temp:
    build = Path(temp)
    obj, wasm = build / "bench.o", build / "atlas.wasm"
    subprocess.run([args.zig, "c++", "-target", "wasm32-wasi", "-std=c++17", "-Oz",
                    "-fno-exceptions", "-fno-rtti", "-c", str(root / "firmware/tests/bench.cpp"),
                    "-o", str(obj)], check=True)
    subprocess.run([args.zig, "wasm-ld", "--no-entry", "--export-dynamic",
                    "--allow-undefined", "--strip-all", str(obj), "-o", str(wasm)], check=True)
    os.replace(wasm, assets / "atlas.wasm")
