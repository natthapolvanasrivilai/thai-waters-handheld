"""Verify the extracted Thai Waters USB preview before writing four named images."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


LAYOUT = {
    "flash/bootloader.bin": 0x0000,
    "flash/partitions.bin": 0x8000,
    "flash/boot_app0.bin": 0xE000,
    "flash/ThaiWaters.bin": 0x10000,
}


def verified_images(root):
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["chip"] != "esp32s3" or manifest["version"] != "0.9.4-controller-preview":
        raise ValueError("unexpected image target or version")
    images = manifest["images"]
    if len(images) != len(LAYOUT) or {i["path"]: i["offset"] for i in images} != LAYOUT:
        raise ValueError("unexpected image layout")
    segments = []
    for image in sorted(images, key=lambda i: i["offset"]):
        path = root / image["path"]
        data = path.read_bytes()
        if len(data) != image["bytes"] or hashlib.sha256(data).hexdigest() != image["sha256"]:
            raise ValueError(f"{path.name} failed integrity verification")
        segments.extend((hex(image["offset"]), str(path)))
    card = manifest["card"]
    if card["path"] != "sdcard/TW-FISH.BIN":
        raise ValueError("unexpected field-art path")
    pixels = (root / card["path"]).read_bytes()
    if len(pixels) != card["bytes"] or hashlib.sha256(pixels).hexdigest() != card["sha256"]:
        raise ValueError("field-art file failed integrity verification")
    return segments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="verify package integrity offline")
    mode.add_argument("--port", help="write to the connected Waveshare 31137 on this serial port")
    args = parser.parse_args()
    try:
        segments = verified_images(Path(__file__).resolve().parent)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        parser.exit(1, f"Cannot use this package: {exc}\n")
    print("Verified four ESP32-S3 flash images and the SD field-art file.", flush=True)
    if args.port:
        return subprocess.call([sys.executable, "-m", "esptool", "--chip", "esp32s3",
                                "--port", args.port, "write-flash", *segments])
    return 0


if __name__ == "__main__":
    sys.exit(main())
