"""Build/verify the local-only Pocket Reel Solo wrapper from a verified browser ZIP."""
import argparse
from base64 import b64encode
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import stat
import zipfile

HTML, WASM, LAND, BUILD, SUMS = "Thai-Waters-play.html", "atlas.wasm", "landscape.wasm", "BUILD.txt", "SHA256SUMS"
LAUNCHER, MANIFEST = "Start-Pocket-Reel-Solo.mjs", "Pocket-Reel-HTML.sha256"
README = "README.txt"
OUTPUT_ORDER = (LAUNCHER, HTML, MANIFEST, README)
INPUT_LIMITS = {HTML: 64 << 20, WASM: 16 << 20, LAND: 16 << 20, BUILD: 1024, SUMS: 1024}
LAUNCHER_SHA = "0b0791dcb8bcb5c5a049eff2d56b4e535a56e54e20ea1569506d424691006705"
DATE = (1980, 1, 1, 0, 0, 0)

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_regular(path, ceiling):
    p = Path(path)
    st = p.lstat()
    require(stat.S_ISREG(st.st_mode) and 0 < st.st_size <= ceiling, "invalid input file")
    data = p.read_bytes()
    require(len(data) == st.st_size, "input changed during read")
    return data

def members(blob, limits, *, ordered=False):
    with zipfile.ZipFile(BytesIO(blob)) as archive:
        infos = archive.infolist()
        names = [i.orig_filename for i in infos]
        require(len(names) == len(set(names)), "duplicate archive member")
        require(set(names) == set(limits) and (not ordered or names == list(limits)), "unexpected archive names/order")
        for entry in infos:
            kind = stat.S_IFMT(entry.external_attr >> 16)
            require(not entry.is_dir() and kind in (0, stat.S_IFREG) and not (entry.flag_bits & 1), "non-regular archive member")
            require(0 < entry.file_size <= limits[entry.orig_filename], "invalid archive member size")
        return {info.orig_filename: archive.read(info) for info in infos}

def load_browser(blob, source, expected_outer):
    require(re.fullmatch(r"[0-9a-f]{40}", source), "invalid expected source")
    require(re.fullmatch(r"[0-9a-f]{64}", expected_outer) and digest(blob) == expected_outer, "browser archive SHA mismatch")
    bundle = members(blob, INPUT_LIMITS)
    require(bundle[BUILD].partition(b"\n")[0] == ("SOURCE_COMMIT=" + source).encode(), "BUILD source mismatch")
    canonical = "".join(digest(bundle[k]) + "  " + k + "\n" for k in (HTML, WASM, LAND, BUILD))
    require(bundle[SUMS] == canonical.encode("ascii"), "inner checksum manifest mismatch")
    require(bundle[WASM] != bundle[LAND], "distinct WASM modules required")
    slots = {WASM: b"const bytes=Uint8Array.from(atob('",
             LAND: b"const sceneryBytes=Uint8Array.from(atob('"}
    for name, slot in slots.items():
        encoded = b64encode(bundle[name])
        require(bundle[name].startswith(b"\0asm\x01\0\0\0") and
                bundle[HTML].count(encoded) == 1 and
                bundle[HTML].count(slot) == 1 and
                slot + encoded + b"'),c=>c.charCodeAt" in bundle[HTML],
                f"embedded WASM mismatch: {name}")
    return bundle

def build(bundle, launcher, readme):
    require(digest(launcher) == LAUNCHER_SHA, "launcher SHA mismatch")
    require(b"\r" not in readme and readme.endswith(b"\n"), "README must use canonical LF")
    body = {LAUNCHER: launcher, HTML: bundle[HTML], MANIFEST: (digest(bundle[HTML]) + "  " + HTML + "\n").encode("ascii"), README: readme}
    out = BytesIO()
    # Stored (not deflated) also makes output independent of zlib versions.
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in OUTPUT_ORDER:
            entry = zipfile.ZipInfo(name, DATE)
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(entry, body[name])
    return out.getvalue()

def validate(candidate, bundle, launcher, readme):
    limits = {LAUNCHER: 64 << 10, HTML: INPUT_LIMITS[HTML], MANIFEST: 100, README: 16 << 10}
    wrapped = members(candidate, limits, ordered=True)
    require(wrapped[HTML] == bundle[HTML] and wrapped[LAUNCHER] == launcher, "wrapper payload mismatch")
    require(wrapped[MANIFEST] == (digest(bundle[HTML]) + "  " + HTML + "\n").encode("ascii"), "wrapper checksum mismatch")
    require(candidate == build(bundle, launcher, readme), "wrapper metadata/encoding mismatch")
    return digest(candidate)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation", choices=("build", "verify"))
    p.add_argument("--browser", required=True, type=Path)
    p.add_argument("--browser-sha256", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    try:
        browser = load_browser(read_regular(a.browser, 90 << 20), a.source, a.browser_sha256)
        sibling = Path(__file__).parent
        launcher = read_regular(sibling / LAUNCHER, 64 << 10)
        readme = read_regular(sibling / README, 16 << 10)
        candidate = build(browser, launcher, readme) if a.operation == "build" else read_regular(a.output, 70 << 20)
        wrapper_sha = validate(candidate, browser, launcher, readme)
        if a.operation == "build":
            with a.output.open("xb") as fd:
                fd.write(candidate)
        print(json.dumps({"source": a.source, "browserArchiveSha256": a.browser_sha256, "htmlSha256": digest(browser[HTML]),
                          "atlasSha256": digest(browser[WASM]), "landscapeSha256": digest(browser[LAND]), "launcherSha256": digest(launcher),
                          "wrapperZipSha256": wrapper_sha, "wrapperMembersOrdered": OUTPUT_ORDER,
                          "evidence": "local-package-integrity-only"}))
    except (ValueError, OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as e:
        p.exit(1, f"Package rejected: {e}\n")

if __name__ == "__main__":
    main()
