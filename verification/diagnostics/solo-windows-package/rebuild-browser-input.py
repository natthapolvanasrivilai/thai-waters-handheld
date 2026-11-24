import hashlib
from pathlib import Path
import sys
import zipfile

out, source_path = map(Path, sys.argv[1:])
expected = {
    "Thai-Waters-play.html": ("game/Thai-Waters-play.html", "0f87d0c63afd86d97602b401967a8c13d75aabfda9a674e6d16a17efc3457f2e"),
    "atlas.wasm": ("game/assets/atlas.wasm", "80b88fca6773b7c348a43e2cb5f1e8ad0478e77ce8790e1de53eb479e946bf2d"),
    "landscape.wasm": ("game/assets/landscape.wasm", "e7d84c41d04f94b0065f64708f8061a6cacc825d2a7cae5983aad516a2a84cfb"),
}
inputs = {}
for name, (path, sha) in expected.items():
    raw = (source_path / path).read_bytes()
    if name.endswith(".html"):
        raw = raw.replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != sha:
        raise SystemExit(f"Exact f08 component mismatch: {name}")
    inputs[name] = raw
inputs["BUILD.txt"] = b"SOURCE_COMMIT=f08e82693c259f505d848f91298bd60ae239d662\n0.13.0\n"
inputs["SHA256SUMS"] = "".join(f"{hashlib.sha256(raw).hexdigest()}  {name}\n"
                              for name, raw in inputs.items()).encode("ascii")
with zipfile.ZipFile(out, "x", compression=zipfile.ZIP_STORED) as z:
    for name, raw in inputs.items():
        entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
        entry.create_system = 3
        entry.external_attr = 0o100644 << 16
        z.writestr(entry, raw)
