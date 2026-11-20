"""Run the canonical Thai Waters browser checks in isolated CI shards."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

SHARDS = {
    "arrival": ("arrival",),
    "gameplay": ("gameplay", "detents", "rumble", "bait", "cast-water", "fish-hints", "handheld-input", "recovered-items"),
    "device": ("device", "lcd", "career-flow", "career-storage", "reload-trace-unit", "mobile-input", "aim-input", "finger-targets", "tackle-hud", "menu-pages", "mobile-display-unit", "screen-layout"),
    "world": ("scenery", "ambient", "mobile-audio", "landing-audio", "hosted-startup", "tournament",
              "thai-catch", "thai-species-names", "gallery-history", "specimen-art"),
}
SITE = ("game/sites/test.mjs", "game/sites/cup-test.mjs")


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def partition(root):
    package = root / "verification/browser-tests/package.json"
    canonical = json.loads(package.read_text())["scripts"]["test"].split(" && ")
    require(all(re.fullmatch(r"node [a-z0-9-]+\.cjs", x) for x in canonical), "Unknown canonical command")
    expected = collections.Counter(x[5:] for x in canonical)
    actual = collections.Counter(n + ".cjs" for tests in SHARDS.values() for n in tests)
    require(actual == expected and all(n == 1 for n in actual.values()),
            f"Shard partition mismatch: missing={expected - actual}, extra={actual - expected}")
    parts = {s: tuple("verification/browser-tests/" + n + ".cjs" for n in tests)
             for s, tests in SHARDS.items()}
    parts["world"] += SITE
    for tests in parts.values():
        for name in tests:
            require((root / name).is_file(), f"Missing script {name}")
    return parts


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(bundle):
    src = os.environ["SOURCE_SHA"]
    require(re.fullmatch(r"[0-9a-f]{40}", src), "Bad source SHA")
    require((bundle / "BUILD.txt").read_text().splitlines()[0] == "SOURCE_COMMIT=" + src,
            "Artifact source mismatch")
    return {"source": src, "html": digest(bundle / "Thai-Waters-play.html"), "wasm": digest(bundle / "atlas.wasm")}


def run(root, shard, bundle, diagnostics):
    tests = partition(root)[shard]
    expected = identity(bundle)
    actual = (digest(root / "game/Thai-Waters-play.html"), digest(root / "game/assets/atlas.wasm"))
    require(actual == (expected["html"], expected["wasm"]), "Checkout artifact differs from staged build")
    diagnostics.mkdir(parents=True, exist_ok=True)
    results = []
    for name in tests:
        path = root / name
        started = time.monotonic()
        log = diagnostics / (path.name + ".log")
        print(f"Run {name}", flush=True)
        with log.open("wb") as output:
            code = subprocess.run(["node", path.name if name.endswith(".cjs") else name],
                                  cwd=path.parent if name.endswith(".cjs") else root,
                                  stdout=output, stderr=subprocess.STDOUT).returncode
        print(f"{name}: exit {code}, {time.monotonic() - started:.1f}s", flush=True)
        if code:
            print(log.read_text(errors="replace")[-4000:], flush=True)
        results.append({"test": name, "exit": code, "seconds": round(time.monotonic() - started, 2)})
        report = dict(expected, shard=shard, results=results)
        (diagnostics / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    require(all(r["exit"] == 0 for r in results), "At least one test failed")


def verify(root, bundle, diagnostics):
    expected = identity(bundle)
    parts = partition(root)
    for shard, tests in parts.items():
        report_path = diagnostics / ("browser-report-" + expected["source"] + "-" + shard) / "report.json"
        require(report_path.is_file(), f"Missing report for {shard}")
        report = json.loads(report_path.read_text())
        require(all(report.get(k) == v for k, v in expected.items()) and report.get("shard") == shard,
                f"Mismatched provenance for {shard}")
        results = report.get("results", [])
        require(tuple(r.get("test") for r in results) == tests, f"Incomplete or duplicate results for {shard}")
        require(all(type(r.get("exit")) is int and r["exit"] == 0 for r in results),
                f"Failed tests for {shard}")
    print(f"Verified {sum(map(len, parts.values()))} exact-source tests across {len(parts)} shards")


def main():
    args = argparse.ArgumentParser()
    args.add_argument("action", choices=["partition", "run", "verify"])
    args.add_argument("--root", type=Path, default=Path.cwd())
    args.add_argument("--bundle", type=Path)
    args.add_argument("--diagnostics", type=Path)
    args.add_argument("--shard", choices=SHARDS)
    setup = args.parse_args()
    if setup.action == "partition":
        print(json.dumps(partition(setup.root), indent=2))
    elif setup.action == "run":
        run(setup.root, setup.shard, setup.bundle, setup.diagnostics)
    else:
        verify(setup.root, setup.bundle, setup.diagnostics)


if __name__ == "__main__":
    main()
