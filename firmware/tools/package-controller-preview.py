"""Build the private USB preview archive using an Arduino CLI build and its merged reference."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("build", "boot-app0", "dependencies", "verification", "output"):
        parser.add_argument("--" + arg, required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    merged = (args.build / "WillowCreek.ino.merged.bin").read_bytes()
    parts = [
        ("flash/bootloader.bin", 0x0000, args.build / "WillowCreek.ino.bootloader.bin"),
        ("flash/partitions.bin", 0x8000, args.build / "WillowCreek.ino.partitions.bin"),
        ("flash/boot_app0.bin", 0xE000, args.boot_app0),
        ("flash/ThaiWaters.bin", 0x10000, args.build / "WillowCreek.ino.bin"),
    ]
    manifest = {"version": "0.9.3-controller-preview", "chip": "esp32s3",
                "board": "Waveshare 31137, Rev F sensor pinout, 16 MB flash and OPI PSRAM",
                "arduino_esp32": "3.3.10", "distribution": "private USB preview",
                "images": [], "source_sha256": {}}
    for source in sorted((root / "WillowCreek").iterdir()):
        if not source.is_file():
            continue
        snapshot = args.build / "sketch" / (source.name + ".cpp" if source.suffix == ".ino" else source.name)
        # Arduino adds line markers and prototypes. Every original source line
        # must appear in the same order in the build snapshot.
        compiled = iter(snapshot.read_text(encoding="utf-8-sig").splitlines())
        for line in source.read_text(encoding="utf-8-sig").splitlines():
            if line and not any(line == other for other in compiled):
                raise ValueError(f"source changed after compilation: {source.name}")
        manifest["source_sha256"]["firmware/WillowCreek/" + source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
    package = {}
    for name, offset, path in parts:
        data = path.read_bytes()
        if not data or merged[offset:offset + len(data)] != data:
            raise ValueError(f"{name} disagrees with the Arduino-merged image at {offset:#x}")
        manifest["images"].append({"path": name, "offset": offset, "bytes": len(data),
                                   "sha256": hashlib.sha256(data).hexdigest()})
        package[name] = data
    package["manifest.json"] = json.dumps(manifest, indent=2).encode() + b"\n"
    package["README.md"] = (root / "Phone-controller.md").read_bytes()
    package["Interfaces.md"] = (root / "Interfaces.md").read_bytes()
    ble = args.boot_app0.resolve().parents[2] / "libraries/BLE"
    for name in ("NOTICE", "LICENSE"):
        package["licenses/Arduino-ESP32-BLE-" + name + ".txt"] = (ble / name).read_bytes()
    package["flash-controller-preview.py"] = (root / "tools/flash-controller-preview.py").read_bytes()
    for part in ("WillowCreek", "tests", "tools"):
        for path in (root / part).rglob("*"):
            if path.is_file() and path.suffix in (".h", ".cpp", ".ino", ".py", ".mjs"):
                package["firmware/" + path.relative_to(root).as_posix()] = path.read_bytes()
    for name in ("Interfaces.md", "README.md", "Phone-controller.md"):
        package["firmware/" + name] = (root / name).read_bytes()
    # Use the exact board libraries and font-license package shipped with baseline 0.9.
    for name in ('field-evidence.md','thai-field-datasets.csv','thai-field-evidence.csv'):
        package['credits/'+name]=(root.parent/'game/content'/name).read_bytes()
    with ZipFile(args.dependencies) as deps:
        for name in deps.namelist():
            if name.startswith(("libraries/", "licenses/", "font-source/")) and not name.endswith("/"):
                package[name] = deps.read(name)
    for path in sorted(args.verification.iterdir()):
        if path.is_file() and path.suffix in (".log", ".txt"):
            package["verification/" + path.name] = path.read_bytes()
    with ZipFile(args.output, "w", ZIP_DEFLATED, compresslevel=6) as result:
        for name, data in sorted(package.items()):
            info = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            result.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=6)
    with ZipFile(args.output) as result:
        if result.testzip() is not None:
            raise ValueError("archive failed CRC verification")
        for entry in manifest["images"]:
            if hashlib.sha256(result.read(entry["path"])).hexdigest() != entry["sha256"]:
                raise ValueError("archived image failed verification")
    print(f"Verified {args.output} ({args.output.stat().st_size:,} bytes)")
    print("SHA256", hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
