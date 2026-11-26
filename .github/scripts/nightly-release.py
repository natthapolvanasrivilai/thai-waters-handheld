"""Package exact verified artifacts as non-release nightly checkpoints."""
import argparse
import base64
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from zoneinfo import ZoneInfo


BROWSER = ("Thai-Waters-play.html", "atlas.wasm", "landscape.wasm", "BUILD.txt")
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"[0-9a-f]{64}")


def require(ok, error):
    if not ok:
        raise ValueError(error)


def sha256(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def checks(directory, names):
    expected = {name: sha256(directory / name) for name in names}
    lines = (directory / "SHA256SUMS").read_text().splitlines()
    require(len(lines) == len(expected), "Unexpected checksum entries")
    require(set(lines) == {f"{digest}  {name}" for name, digest in expected.items()}, "Artifact checksum mismatch")


def prepare(browser, controller, out, sha):
    require(SHA.fullmatch(sha), "Invalid source commit")
    source = f"SOURCE_COMMIT={sha}"
    short = sha[:7]
    checks(browser, BROWSER)
    require((browser / "BUILD.txt").read_text().splitlines()[0] == source, "Wrong browser commit")
    html = (browser / BROWSER[0]).read_bytes()
    for name in ("atlas.wasm", "landscape.wasm"):
        wasm = (browser / name).read_bytes()
        require(wasm.startswith(b"\0asm"), f"Bad WASM header: {name}")
        require(html.count(base64.b64encode(wasm)) == 1, f"Standalone HTML and {name} differ")

    controller_name = f"Thai-Waters-controller-{short}.zip"
    folder = controller / "release-controller"
    checks(folder, (controller_name,))
    require((controller / "verify/source.txt").read_text().strip() == source, "Wrong controller source record")
    with ZipFile(folder / controller_name) as z:
        require(z.testzip() is None, "Bad controller ZIP members")
        require(z.read("verification/source.txt").decode().strip() == source, "Wrong packed controller commit")
        require(0 < z.getinfo("flash/ThaiWaters.bin").file_size <= 3145728, "Controller partition limit")

    out.mkdir()
    browser_name = f"Thai-Waters-browser-{short}.zip"
    with ZipFile(out / browser_name, "w", compression=ZIP_DEFLATED) as z:
        for name in (*BROWSER, "SHA256SUMS"):
            z.writestr(ZipInfo(name, (2026, 1, 1, 0, 0, 0)), (browser / name).read_bytes(), compress_type=ZIP_DEFLATED)
    shutil.copyfile(folder / controller_name, out / controller_name)
    names = (browser_name, controller_name)
    sums = "".join(f"{sha256(out / name)}  {name}\n" for name in names)
    (out / "SHA256SUMS").write_text(sums)
    return {name: sha256(out / name) for name in (*names, "SHA256SUMS")}


def guard(env, meta, sha):
    require(SHA.fullmatch(sha) and env.get("GITHUB_SHA") == sha, "Nightly checkout SHA mismatch")
    require(env.get("GITHUB_EVENT_NAME") == "schedule", "Only scheduled runs may publish")
    require(meta.get("private") is True, "Nightly repository is not private")
    require(env.get("GITHUB_REF") == "refs/heads/" + meta["default_branch"], "Nightly is not on default branch")


def release_assets(assets):
    result = {}
    for asset in assets:
        name = asset["name"]
        digest = asset.get("digest") or ""
        require(name not in result and asset["state"] == "uploaded" and asset["size"] > 0, "Incomplete or duplicate release assets")
        require(digest.startswith("sha256:") and DIGEST.fullmatch(digest[7:]), "Missing or invalid release asset digest")
        result[name] = digest[7:]
    return result


def gh(*args):
    return subprocess.run(["gh", *args], check=True, text=True, stdout=subprocess.PIPE).stdout


def api(path, *args):
    return json.loads(gh("api", path, *args))


def verify_tag(base, tag, sha):
    tagref = api(f"{base}/git/ref/tags/{tag}")["object"]
    require(tagref["type"] == "commit" and tagref["sha"] == sha, "Nightly tag is not pinned to exact commit")


def publish(browser, controller, out, sha, env):
    raise ValueError("Nightly publication disabled: every release requires the tagged handbook gate")


if __name__ == "__main__":
    arg = argparse.ArgumentParser()
    arg.add_argument("action", choices=("prepare", "publish"))
    arg.add_argument("browser", type=Path)
    arg.add_argument("controller", type=Path)
    arg.add_argument("out", type=Path)
    arg.add_argument("sha")
    a = arg.parse_args()
    if a.action == "prepare":
        print(json.dumps(prepare(a.browser, a.controller, a.out, a.sha), sort_keys=True))
    else:
        publish(a.browser, a.controller, a.out, a.sha, os.environ)
