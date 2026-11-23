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
    "device": ("device", "lcd", "career-flow", "career-storage", "file-career-offline", "reload-trace-unit", "mobile-input", "aim-input", "finger-targets", "tackle-hud", "menu-pages", "location-map-unit", "location-map", "mobile-display-unit", "screen-layout"),
    "world": ("scenery", "ambient", "mobile-audio", "landing-audio", "hosted-startup", "tournament",
              "thai-catch", "thai-species-names", "gallery-history", "collection-native", "specimen-art"),
}
LANDSCAPE_TESTS = {"verification/browser-tests/scenery.cjs", "verification/browser-tests/ambient.cjs"}
SITE = ("game/sites/test.mjs", "game/sites/cup-test.mjs")
PERSISTENCE_LANES = {
    **{f"verification/browser-tests/{name}.cjs": "loopback" for name in (
        "arrival", "gameplay", "career-flow", "rumble", "aim-input", "landing-audio",
        "bait", "gallery-history", "specimen-art",
    )},
    "verification/browser-tests/file-career-offline.cjs": "file",
    "verification/browser-tests/location-map.cjs": "file",
}



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
    require(PERSISTENCE_LANES.keys() <= {name for tests in parts.values() for name in tests},
            "A required persistence lane is not assigned to a shard")
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
    return {"source": src, "html": digest(bundle / "Thai-Waters-play.html"), "wasm": digest(bundle / "atlas.wasm"),
            "landscape": digest(bundle / "landscape.wasm")}


# Last reviewed source before direct landscape fixture receipts were required.
LEGACY_LANDSCAPE_END = "e5203606efd67186bdf144ab4ac3d6c2acab6638"


def landscape_proof_mode(root, bundle, source):
    git = ["git", "-C", str(root)]
    def tracked_has_marker(path):
        checked_in = subprocess.check_output([*git, "show", f"{source}:{path}"])
        return b"TW_LANDSCAPE " in checked_in
    caps = [tracked_has_marker(path) for path in sorted(LANDSCAPE_TESTS)]
    require(len(set(caps)) == 1, "Mixed checked-in landscape proof capabilities")
    wasm = bundle / "landscape.wasm"
    n = subprocess.check_output(["node", "-e",
        "const m=new WebAssembly.Module(require('node:fs').readFileSync(process.argv[1]));"
        "console.log(new WebAssembly.Instance(m).exports.sampleAmbient.length)", str(wasm)], text=True).strip()
    if all(caps):
        require(n == "3", "Direct landscape proof requires the new game ABI")
        return "direct-world"
    require(n == "2", "New landscape ABI requires direct proof from both world tests")
    require(subprocess.run([*git, "merge-base", "--is-ancestor", source, LEGACY_LANDSCAPE_END],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
            "Missing direct landscape proof on an unverified historical source")
    return "historical-artifact-only"


def lane_evidence(log, name, html):
    lane = PERSISTENCE_LANES.get(name)
    exact = [f"TW_LANE {lane} {html}"] if lane else []
    found = [line for line in log.splitlines() if line.startswith("TW_LANE ")]
    return found == exact


def run(root, shard, bundle, diagnostics):
    tests = partition(root)[shard]
    expected = identity(bundle)
    expected["landscapeProof"] = landscape_proof_mode(root, bundle, expected["source"])
    direct = expected["landscapeProof"] == "direct-world"
    print("Landscape proof mode: " + expected["landscapeProof"], flush=True)
    actual = (digest(root / "game/Thai-Waters-play.html"), digest(root / "game/assets/atlas.wasm"),
              digest(root / "game/assets/landscape.wasm"))
    require(actual == (expected["html"], expected["wasm"], expected["landscape"]), "Checkout artifact differs from staged build")
    diagnostics.mkdir(parents=True, exist_ok=True)
    results = []
    for name in tests:
        path = root / name
        started = time.monotonic()
        log = diagnostics / (path.name + ".log")
        print(f"Run {name}", flush=True)
        test_env = None
        if path.name == "gallery-history.cjs":
            test_env = dict(os.environ, COLLECTION_PREVIEW=str((diagnostics / "collection-eight-portrait.png").resolve()))
        if path.name == "collection-native.cjs":
            test_env = dict(os.environ, NATIVE_HTML_SHA256=expected["html"],
                            NATIVE_OUT=str((diagnostics / "collection-native").resolve()))
        with log.open("wb") as output:
            code = subprocess.run(["node", path.name if name.endswith(".cjs") else name], env=test_env,
                                  cwd=path.parent if name.endswith(".cjs") else root,
                                  stdout=output, stderr=subprocess.STDOUT).returncode
        output = log.read_text(errors="replace")
        lane = PERSISTENCE_LANES.get(name)
        observed = lane_evidence(output, name, expected["html"])
        if not observed:
            print(f"{name}: missing, duplicate, or incorrect browser lane proof", flush=True)
            if code == 0:
                code = 1
        landscape_observed = [line for line in output.splitlines() if line.startswith("TW_LANDSCAPE ")]
        if name in LANDSCAPE_TESTS and landscape_observed != (["TW_LANDSCAPE " + expected["landscape"]] if direct else []):
            print(f"{name}: missing, duplicate, or incorrect directly tested landscape hash", flush=True)
            if code == 0:
                code = 1
        print(f"{name}: exit {code}, {time.monotonic() - started:.1f}s", flush=True)
        if code:
            print(output[-4000:], flush=True)
        result = {"test": name, "exit": code, "seconds": round(time.monotonic() - started, 2)}
        if lane and observed:
            result["lane"] = lane
        if direct and name in LANDSCAPE_TESTS and code == 0:
            result["landscape"] = expected["landscape"]
        results.append(result)
        report = dict(expected, shard=shard, results=results)
        (diagnostics / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    require(all(r["exit"] == 0 for r in results), "At least one test failed")


def verify(root, bundle, diagnostics):
    expected = identity(bundle)
    expected["landscapeProof"] = landscape_proof_mode(root, bundle, expected["source"])
    direct = expected["landscapeProof"] == "direct-world"
    print("Landscape proof mode: " + expected["landscapeProof"], flush=True)
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
        require(all(r.get("lane") == PERSISTENCE_LANES.get(r["test"]) for r in results),
                f"Missing or incorrect persistence lane for {shard}")
        require(all(r.get("landscape") == (expected["landscape"] if direct and r["test"] in LANDSCAPE_TESTS else None)
                    for r in results), f"Missing or incorrect directly tested landscape hash for {shard}")
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
