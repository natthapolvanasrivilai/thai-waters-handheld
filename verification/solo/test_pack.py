import io
from pathlib import Path
import unittest
import zipfile
from base64 import b64encode
import pack


SOURCE = "a" * 40
MODULE = b"\0asm\x01\0\0\0"
ATLAS = MODULE
LANDSCAPE = MODULE + b"\0\x02\x01a"
ROOT = Path(__file__).parent


def page(atlas, land):
    return (b"const bytes=Uint8Array.from(atob('" + b64encode(atlas) +
            b"'),c=>c.charCodeAt(0));\nconst sceneryBytes=Uint8Array.from(atob('" +
            b64encode(land) + b"'),c=>c.charCodeAt(0));")


def fixture(*, html=None, atlas=ATLAS, land=LANDSCAPE, source=SOURCE, extra=None):
    if html is None:
        html = page(atlas, land)
    payload = {
        pack.HTML: html, pack.WASM: atlas, pack.LAND: land,
        pack.BUILD: ("SOURCE_COMMIT=" + source + "\nfixture\n").encode(),
    }
    payload[pack.SUMS] = "".join(
        pack.digest(payload[k]) + "  " + k + "\n"
        for k in (pack.HTML, pack.WASM, pack.LAND, pack.BUILD)
    ).encode()
    if extra:
        payload.update(extra)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for key, value in payload.items():
            z.writestr(key, value)
    return out.getvalue()


class SoloPackaging(unittest.TestCase):
    def load(self, blob):
        return pack.load_browser(blob, SOURCE, pack.digest(blob))

    def setUp(self):
        self.launcher = (ROOT / pack.LAUNCHER).read_bytes()
        self.readme = (ROOT / pack.README).read_bytes()

    def test_exact_html_and_deterministic_wrapper(self):
        bundle = self.load(fixture())
        w = pack.build(bundle, self.launcher, self.readme)
        self.assertEqual(w, pack.build(bundle, self.launcher, self.readme))
        self.assertEqual(pack.digest(w), pack.validate(w, bundle, self.launcher, self.readme))
        with zipfile.ZipFile(io.BytesIO(w)) as z:
            self.assertEqual(tuple(z.namelist()), pack.OUTPUT_ORDER)
            self.assertEqual(z.read(pack.HTML), bundle[pack.HTML])
        with self.assertRaisesRegex(ValueError, "metadata"):
            pack.validate(w + b"appended", bundle, self.launcher, self.readme)

    def test_source_outer_checksum_and_noncanonical_names(self):
        blob = fixture()
        with self.assertRaisesRegex(ValueError, "source mismatch"):
            self.load(fixture(source="b" * 40))
        with self.assertRaisesRegex(ValueError, "archive SHA"):
            pack.load_browser(blob, SOURCE, "1" * 64)
        with self.assertRaisesRegex(ValueError, "unexpected archive"):
            self.load(fixture(extra={"../extra": b"x"}))

    def test_recomputed_hashes_do_not_mask_missing_or_duplicate_wasm(self):
        with self.assertRaisesRegex(ValueError, "embedded WASM mismatch: landscape"):
            self.load(fixture(html=page(ATLAS, LANDSCAPE).replace(b64encode(LANDSCAPE), b"missing")))
        with self.assertRaisesRegex(ValueError, "distinct WASM"):
            self.load(fixture(land=ATLAS))
        with self.assertRaisesRegex(ValueError, "embedded WASM mismatch: atlas"):
            self.load(fixture(html=page(ATLAS, LANDSCAPE) + b64encode(ATLAS)))
        with self.assertRaisesRegex(ValueError, "embedded WASM mismatch: atlas"):
            self.load(fixture(html=page(LANDSCAPE, ATLAS)))

    def test_readme_lf_is_required_and_pinned_in_git(self):
        self.assertIn("README.txt text eol=lf", (ROOT / ".gitattributes").read_text())
        with self.assertRaisesRegex(ValueError, "canonical LF"):
            pack.build(self.load(fixture()), self.launcher, self.readme.replace(b"\n", b"\r\n"))

    def test_launcher_cannot_be_silently_replaced_or_crlf_converted(self):
        bundle = self.load(fixture())
        for payload in (self.launcher + b"\n", self.launcher.replace(b"\n", b"\r\n")):
            with self.subTest(payloadBytes=len(payload)):
                with self.assertRaisesRegex(ValueError, "launcher SHA"):
                    pack.build(bundle, payload, self.readme)


if __name__ == "__main__":
    unittest.main()
