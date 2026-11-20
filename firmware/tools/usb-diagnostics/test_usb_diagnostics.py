"""Host-only tests. Every transport and reading here is SYNTHETIC."""
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import usb_diagnostics as d

CAPS = dict(api=1, minor=0, board="riffle-e-31137", fw=6,
            inputs=["accel_raw", "gyro_raw", "reel_counts"], stream_hz=10)
SAMPLE = dict(api=1, ms=123, accel_ok=1, gyro_ok=0, accel_g=[0., 1., 0.],
              gyro_dps=[0., 0., 0.], accel_raw=[0, 8192, 0], gyro_raw=[0, 0, 0],
              field=4, reel_counts=4095)


def wire(data):
    return json.dumps(data).encode() + b"\n"


class SyntheticSerial:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def read_until(self, terminator, size):
        line = next(self.replies, b"")
        if isinstance(line, Exception):
            raise line
        return line


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.t = 0
        def clock():
            self.t += .05
            return self.t
        binding = patch.object(d.time, "monotonic", side_effect=clock)
        binding.start()
        self.addCleanup(binding.stop)

    def test_published_fixture_wrap_dropout_and_no_false_zeros(self):
        with (Path(__file__).parent / "fixtures" / "synthetic-wrap-dropout.jsonl").open() as f:
            report = d.validate(f)
        self.assertEqual(report, {"source": "SYNTHETIC", "samples": 5,
                                  "reel_valid": 4, "gyro_valid": 3, "complete": True})
        self.assertFalse(d.validate(io.StringIO(""))["complete"])

    def test_one_sample_and_ignored_diagnostics(self):
        serial = SyntheticSerial([b"old password diagnostic\n", wire(CAPS), wire(SAMPLE)])
        trace = []
        d.capture(serial, None, trace.append)
        self.assertEqual(serial.writes, list(d.COMMANDS[:2]))
        self.assertEqual([x["kind"] for x in trace], ["caps", "sample", "end"])
        self.assertEqual(trace[1]["data"]["reel_counts"], 4095)
        self.assertTrue(all(trace[1]["data"][key] is None for key in d.UNAVAILABLE))
        self.assertIsNone(trace[1]["data"]["gyro_raw"])
        self.assertNotIn("password", str(trace))

    def test_bad_caps_never_streams(self):
        serial = SyntheticSerial([wire(dict(CAPS, board="wrong-board"))])
        trace = []
        with self.assertRaisesRegex(RuntimeError, "No valid"):
            d.capture(serial, 1, trace.append)
        self.assertEqual(serial.writes, [d.COMMANDS[0]])
        self.assertEqual(trace[0]["status"], "incomplete")

    def test_stream_bounded_and_off_ack(self):
        class StreamSerial(SyntheticSerial):
            def read_until(self, terminator, size):
                if self.writes[-1] == d.COMMANDS[3]:
                    return wire({"ok": True})
                return super().read_until(terminator, size)
        serial = StreamSerial([wire(CAPS), wire({"ok": True}), wire(SAMPLE)])
        trace = []
        d.capture(serial, 1, trace.append)
        self.assertEqual(serial.writes, [d.COMMANDS[0], d.COMMANDS[2], d.COMMANDS[3]])
        self.assertTrue(trace[-1]["stream_off_confirmed"])

    def test_disconnect_leaves_incomplete_then_new_session_can_reconnect(self):
        serial = SyntheticSerial([wire(CAPS), wire({"ok": True}),
                                  wire(SAMPLE), OSError("unplugged"), OSError("offline")])
        rows = []
        with self.assertRaisesRegex(OSError, "unplugged"):
            d.capture(serial, 1, rows.append)
        self.assertEqual(serial.writes[-1], d.COMMANDS[3])
        self.assertFalse(rows[-1]["stream_off_confirmed"])
        self.assertEqual(rows[-1]["status"], "incomplete")
        new = SyntheticSerial([wire(CAPS), wire(SAMPLE)])
        rows = []
        d.capture(new, None, rows.append)
        self.assertEqual(rows[0]["seq"], 0)
        self.assertEqual(rows[-1]["status"], "complete")

    def test_unknown_and_invalid_are_not_false_zeroes(self):
        kind, p = d.classify(wire(dict(SAMPLE, field=3, reel_counts=-1, accel_ok=0, accel_g=[])))
        self.assertEqual(kind, "sample")
        self.assertIsNone(p["reel_counts"])
        self.assertIsNone(p["accel_g"])
        for invalid in (dict(SAMPLE, field=3), dict(SAMPLE, gyro_ok=5), dict(SAMPLE, api=2),
                        dict(SAMPLE, reel_counts=4096), dict(SAMPLE, accel_g=[1, 2, float("nan")])):
            self.assertEqual(d.classify(wire(invalid)), (None, None))

    def test_replay_synthetic_order_and_no_extra_fields(self):
        fixture = []
        d.capture(SyntheticSerial([wire(CAPS), wire(SAMPLE)]), None, fixture.append)
        for row in fixture:
            row["source"] = "SYNTHETIC"
            row["never_echo"] = "password"
        fixture[1]["data"]["arbitrary_wire_field"] = "password"
        serialized = [wire(row).decode() for row in fixture]
        output = io.StringIO()
        self.assertTrue(d.replay(io.StringIO("".join(serialized)), output))
        self.assertEqual([json.loads(line)["kind"] for line in output.getvalue().splitlines()],
                         ["caps", "sample", "end"])
        rows = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertTrue(all(x["source"] == "SYNTHETIC" and x["mode"] == "REPLAY" for x in rows))
        self.assertIn("SYNTHETIC", output.getvalue())
        self.assertNotIn("password", output.getvalue())
        self.assertFalse(d.replay(io.StringIO("".join(serialized[:-1])), io.StringIO()))
        with self.assertRaisesRegex(ValueError, "order"):
            d.replay(io.StringIO("".join(serialized[1:])), io.StringIO())

    def test_fragmented_caps_sample_and_ack_share_lf_framer(self):
        caps, sample = wire(CAPS), wire(SAMPLE)
        serial = SyntheticSerial([caps[:17], b"", caps[17:] + sample[:9], sample[9:]])
        rows = []
        d.capture(serial, None, rows.append)
        self.assertEqual([x["kind"] for x in rows], ["caps", "sample", "end"])
        ack = wire({"ok": True})
        serial = SyntheticSerial([caps[:10], caps[10:], ack[:8], b"", ack[8:] + sample[:8], sample[8:]])
        frame = d.LFFramer(serial)
        self.assertEqual(frame.receive("caps", d.time.monotonic() + 1), CAPS)
        self.assertTrue(frame.receive("ack", d.time.monotonic() + 1))
        self.assertEqual(frame.receive("sample", d.time.monotonic() + 1)["reel_counts"], 4095)

    def test_oversized_line_requires_newline_before_json_suffix(self):
        malicious = wire(dict(CAPS, fw=777))
        legitimate = wire(CAPS)
        serial = SyntheticSerial([b"x" * 1024, malicious[:3], b"", malicious[3:], legitimate])
        frame = d.LFFramer(serial)
        self.assertEqual(frame.receive("caps", d.time.monotonic() + 1)["fw"], 6)
        self.assertFalse(frame.discard)

    def test_replay_is_bounded_and_requires_final_lf(self):
        class BeBounded(io.StringIO):
            def readline(self, limit=-1):
                if limit != 4097:
                    raise AssertionError("Unbounded read")
                return super().readline(limit)
        with self.assertRaisesRegex(ValueError, "Oversized"):
            d.replay(BeBounded("x" * 6000 + "\n"), io.StringIO())
        rows = []
        d.capture(SyntheticSerial([wire(CAPS), wire(SAMPLE)]), None, rows.append)
        data = "".join(wire(row).decode() for row in rows)
        with self.assertRaisesRegex(ValueError, "missing its LF"):
            d.replay(BeBounded(data.rstrip("\n")), io.StringIO())
        with self.assertRaisesRegex(ValueError, "missing its LF"):
            d.replay(BeBounded(data.rstrip("\n") + "\r", newline=""), io.StringIO())
        out = io.StringIO()
        self.assertTrue(d.replay(BeBounded(data), out))
        self.assertTrue(all(json.loads(line)["mode"] == "REPLAY" and json.loads(line)["source"] == "LIVE"
                            for line in out.getvalue().splitlines()))

    def test_conflicting_wire_key_is_rejected(self):
        self.assertEqual(d.classify(b'{"api":1,"api":2}\n'), (None, None))


if __name__ == "__main__":
    unittest.main()
