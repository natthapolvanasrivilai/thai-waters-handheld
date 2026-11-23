import base64
import hashlib
import importlib.util
import os
import pathlib
import shutil
import tempfile
import unittest
import zipfile

P = pathlib.Path
SPEC = importlib.util.spec_from_file_location("nightly", P(__file__).with_name("nightly-release.py"))


def sums(path, names):
    (path / "SHA256SUMS").write_text("".join(f"{hashlib.sha256((path / name).read_bytes()).hexdigest()}  {name}\n" for name in names))


class Verify(unittest.TestCase):
    def setUp(self):
        self.n = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(self.n)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = P(self.tmp.name)
        self.sha = "08665bb919b5be42b9ca464e7de84ec59d8980b7"
        self.browser = self.root / "browser"
        self.controller = self.root / "controller"
        self.out = self.root / "out"
        if location := os.environ.get("NIGHTLY_FIXTURE_RUN"):
            shutil.copytree(P(location) / "browser", self.browser)
            shutil.copytree(P(location) / "controller", self.controller)
        else:
            self.browser.mkdir()
            (self.controller / "release-controller").mkdir(parents=True)
            (self.controller / "verify").mkdir()
            record = f"SOURCE_COMMIT={self.sha}\n"
            wasm = b"\0asm\x01\0\0\0"
            (self.browser / "atlas.wasm").write_bytes(wasm)
            landscape = wasm + b"\0\x01\0"  # distinct valid empty custom section
            (self.browser / "landscape.wasm").write_bytes(landscape)
            (self.browser / "Thai-Waters-play.html").write_bytes(b"<script>const wasm='" + base64.b64encode(wasm) + b"', landscape='" + base64.b64encode(landscape) + b"';</script>")
            (self.browser / "BUILD.txt").write_text(record)
            sums(self.browser, ("Thai-Waters-play.html", "atlas.wasm", "landscape.wasm", "BUILD.txt"))
            (self.controller / "verify/source.txt").write_text(record)
            name = "Thai-Waters-controller-08665bb.zip"
            with zipfile.ZipFile(self.controller / "release-controller" / name, "w") as z:
                z.writestr("verification/source.txt", record)
                z.writestr("flash/ThaiWaters.bin", b"fixture")
            sums(self.controller / "release-controller", [name])

    def prepare(self):
        return self.n.prepare(self.browser, self.controller, self.out, self.sha)

    def test_real_bundle(self):
        assets = self.prepare()
        self.assertEqual(sorted(assets), ["SHA256SUMS", "Thai-Waters-browser-08665bb.zip", "Thai-Waters-controller-08665bb.zip"])
        for name, digest in assets.items():
            self.assertEqual(hashlib.sha256((self.out / name).read_bytes()).hexdigest(), digest)
        with zipfile.ZipFile(self.out / "Thai-Waters-browser-08665bb.zip") as z:
            self.assertEqual(set(z.namelist()), {"BUILD.txt", "SHA256SUMS", "Thai-Waters-play.html", "atlas.wasm", "landscape.wasm"})
            self.assertIsNone(z.testzip())

    def test_bad_browser_wasm(self):
        (self.browser / "atlas.wasm").write_bytes(b"not wasm")
        sums(self.browser, ("Thai-Waters-play.html", "atlas.wasm", "landscape.wasm", "BUILD.txt"))
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_rejects_substituted_landscape_even_with_refreshed_sums(self):
        f = self.browser / "landscape.wasm"
        f.write_bytes(f.read_bytes() + b"\0\x01\0")
        sums(self.browser, ("Thai-Waters-play.html", "atlas.wasm", "landscape.wasm", "BUILD.txt"))
        with self.assertRaisesRegex(ValueError, r"HTML.*landscape"):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_rejects_duplicate_embedding_of_either_module(self):
        page = self.browser / "Thai-Waters-play.html"
        original = page.read_bytes()
        for name in ("atlas.wasm", "landscape.wasm"):
            with self.subTest(name=name):
                page.write_bytes(original + base64.b64encode((self.browser / name).read_bytes()))
                sums(self.browser, ("Thai-Waters-play.html", "atlas.wasm", "landscape.wasm", "BUILD.txt"))
                with self.assertRaisesRegex(ValueError, rf"HTML.*{name}"):
                    self.prepare()
                self.assertFalse(self.out.exists())

    def test_rejects_omitted_landscape_checksum(self):
        sums(self.browser, ("Thai-Waters-play.html", "atlas.wasm", "BUILD.txt"))
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_wrong_controller_source(self):
        (self.controller / "verify/source.txt").write_text("SOURCE_COMMIT=" + "a" * 40 + "\n")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.out.exists())

    def test_incomplete_and_mismatched_release_assets(self):
        good = {"a.zip": "a" * 64}
        asset = {"name": "a.zip", "size": 5, "state": "uploaded", "digest": "sha256:" + "a" * 64}
        self.assertEqual(self.n.release_assets([asset]), good)
        with self.assertRaises(ValueError):
            self.n.release_assets([asset, asset])
        with self.assertRaises(ValueError):
            self.n.release_assets([{**asset, "state": "open"}])

    def test_only_scheduled_private_default_branch(self):
        env = {"GITHUB_EVENT_NAME": "schedule", "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": self.sha}
        meta = {"private": True, "default_branch": "main"}
        self.n.guard(env, meta, self.sha)
        for changed in ({"GITHUB_EVENT_NAME": "workflow_dispatch"}, {"GITHUB_REF": "refs/heads/other"}, {"GITHUB_SHA": "a"*40}):
            with self.assertRaises(ValueError):
                self.n.guard({**env, **changed}, meta, self.sha)
        with self.assertRaises(ValueError):
            self.n.guard(env, {**meta, "private": False}, self.sha)


if __name__ == "__main__":
    unittest.main()
