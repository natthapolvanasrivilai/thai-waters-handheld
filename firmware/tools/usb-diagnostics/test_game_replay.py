"""Synthetic host checks; no COM ports or physical devices."""
import copy
import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).parent
DRIVER = HERE / ".local-wheel-replay"
FIXTURE = HERE / "fixtures/synthetic-wrap-dropout.jsonl"

def prep(data):
    return subprocess.run([sys.executable, str(HERE / "prepare_game_replay.py")],
                          input=data, text=True, capture_output=True, cwd=HERE)

def fixture(points, source="SYNTHETIC", status="complete"):
    base = [json.loads(row) for row in FIXTURE.read_text().splitlines()]
    caps = base[0]
    caps["source"] = source
    out = [caps]
    for i, (ms, field, counts) in enumerate(points, 1):
        row = copy.deepcopy(base[1])
        row.update(seq=i, offset_ms=i * 20, source=source)
        row["data"].update(ms=ms, field=field, reel_counts=counts)
        out.append(row)
    out.append(dict(schema=1, seq=len(out), offset_ms=20 * len(out), source=source,
                    kind="end", status=status, samples=len(points), stream_off_confirmed=True))
    return "".join(json.dumps(row) + "\n" for row in out)

class GameReplay(unittest.TestCase):
    def engine(self, text, reverse=False):
        p = prep(text)
        self.assertEqual(p.returncode, 0, p.stderr)
        exe = [str(DRIVER)] + (["--reverse"] if reverse else [])
        r = subprocess.run(exe, input=p.stdout, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [json.loads(line) for line in r.stdout.splitlines()]

    def test_engine_wrap_invalid_rebase_impossible_jump_and_device_reset(self):
        text = fixture([(4294967276,4,4090),(0,4,10),(20,4,4086),(40,3,None),
                        (60,4,650),(80,4,660),(100,4,2500),(120,4,2510),
                        (140,4,2510),(140,4,2510),(5,4,200),(25,4,203),(125,4,208)])
        a = self.engine(text)
        result = [r["counts"] for r in a]
        self.assertEqual(result, [0,16,-20,0,0,10,0,10,0,0,0,3,0])
        self.assertEqual([a[i]["event"] for i in (0,3,4,6,8,9,10,12)],
                         ["baseline","invalid-field","baseline","implausible-delta","accepted",
                          "duplicate-ms","uptime-reset","stale-gap"])
        self.assertEqual([r["counts"] for r in self.engine(text, True)], [-v for v in result])
        self.assertEqual(a, self.engine(text), "same packed bytes replay identically")
        self.assertTrue(all(r["source"] == "SYNTHETIC" and r["mode"] == "REPLAY" for r in a))

    def test_shared_game_line_changes_for_real_engine_turns(self):
        text = fixture([(0,4,4056),(20,4,80),(40,4,200)])
        a, opposite = self.engine(text), self.engine(text, True)
        self.assertEqual(a[-1]["phase"], "Fight")
        self.assertLess(a[-1]["line_milliturns"], opposite[-1]["line_milliturns"])
        self.assertEqual(a[-1]["catches"], 0)

    def test_nominal_api_stream_is_not_a_game_rate_signal(self):
        result = self.engine(FIXTURE.read_text())
        self.assertEqual([x["counts"] for x in result], [0] * 5)
        self.assertEqual(result[2]["event"], "stale-gap")
        self.assertTrue(all(not x["game_applied"] for x in result))

    def test_live_origin_is_retained_without_live_actions(self):
        rows = self.engine(fixture([(0,4,0),(20,4,8)], source="LIVE"))
        self.assertTrue(all(r["source"] == "LIVE" and r["mode"] == "REPLAY" for r in rows))
        self.assertTrue(all(not r["game_applied"] for r in rows))
        self.assertEqual(rows[-1]["counts"], 8)

    def test_prepared_driver_rejects_all_rows_on_bad_numeric_tokens(self):
        for data in ("TW-REEL-REPLAY-1 LIVE 2\n0 3\n-18446744073709551615 4\n",
                     "TW-REEL-REPLAY-1 LIVE 2\n0 3\n2 4 trailing\n",
                     "TW-REEL-REPLAY-1 SYNTHETIC 4097\n"):
            r = subprocess.run([str(DRIVER)], input=data, text=True, capture_output=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "")

    def test_packer_checks_total_sample_bound_before_any_output(self):
        p = prep(fixture([(i * 20,4,i % 4096) for i in range(4097)]))
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")

    def test_incomplete_or_tampered_trace_emits_nothing(self):
        good = fixture([(0,4,30),(20,4,40)])
        for data in (fixture([(0,4,30)], status="incomplete"),
                     good.replace('"seq": 2','"seq": 9'), good[:-1],
                     good.replace('"accel_ok": true','"accel_ok": true, "accel_ok": true')):
            p = prep(data)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(p.stdout, "")

if __name__ == "__main__":
    unittest.main()
