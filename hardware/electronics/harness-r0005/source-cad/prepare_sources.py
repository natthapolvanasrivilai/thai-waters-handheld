"""Verify official CviLux downloads and reconstruct the four local STEP imports."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlparse
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent


def check(data, expected, label):
    if hashlib.sha256(data).hexdigest() != expected:
        raise SystemExit(f"Source changed: {label}. Inspect the revision before continuing.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("downloads", type=Path, help="Folder containing the supplier ZIPs, extracted IGES files or PDFs")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    ledger = json.loads((HERE/"source-manifest.json").read_text())
    for row in ledger["manufacturer_files"]:
        target = HERE/row["file"]
        src = args.downloads/row["file"]
        if src.is_file():
            data = src.read_bytes()
        elif "zip_member" in row:
            package = args.downloads/unquote(Path(urlparse(row["source_url"]).path).name)
            if not package.is_file():
                parser.exit(1, f"Missing {row['file']}. Supplier download: {row['source_url']}\n")
            zipped = package.read_bytes()
            check(zipped,row["zip_sha256"],package.name)
            with ZipFile(io.BytesIO(zipped)) as archive:
                data=archive.read(row["zip_member"])
        else:
            parser.exit(1, f"Missing {row['file']}. Supplier download: {row['source_url']}\n")
        check(data, row["sha256"], row["file"])
        if not args.verify_only and (not target.exists() or target.read_bytes() != data):
            target.write_bytes(data)
    if not args.verify_only:
        with tempfile.TemporaryDirectory() as dst:
            subprocess.run([sys.executable, HERE/"convert_supplier.py", dst], check=True)
            for row in ledger["assembly_imports"]:
                shutil.copyfile(Path(dst)/row["file"], HERE/row["file"])
    print(f"Verified {len(ledger['manufacturer_files'])} supplier inputs")


if __name__ == "__main__":
    main()
