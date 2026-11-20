"""Read-only Pocket Reel API v1 diagnostic capture and offline JSONL replay."""
import argparse
from collections import deque
import json
import math
from pathlib import Path
import re
import sys
import time

COMMANDS = (
    b"api1 caps\n", b"api1 sample\n", b"api1 stream on\n", b"api1 stream off\n",
)
CAP_KEYS = ("api", "minor", "board", "fw", "inputs", "stream_hz")
UNAVAILABLE = ("battery_mv", "battery_percent", "battery_present", "usb_vbus",
               "charging", "touch", "switches", "reel_unwrapped_counts")


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def vector(value, raw):
    def valid(x):
        if raw:
            return integer(x, -32768, 32767)
        return type(x) in (int, float) and abs(x) <= 10000 and math.isfinite(x)
    return isinstance(value, list) and len(value) == 3 and all(map(valid, value))


def json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def classify(line):
    """Keep only these wire fields. Unrelated console/journal rows are not recorded."""
    if len(line) > 1024 or not line.endswith(b"\n") or not line.lstrip().startswith(b"{"):
        return None, None
    try:
        p = json.loads(line, object_pairs_hook=json_object)
        if not isinstance(p, dict):
            return None, None
        if set(p) == {"ok"} and type(p["ok"]) is bool:
            return "ack", p["ok"]
        if not integer(p.get("api"), 1, 1):
            return None, None
        if (p.get("board") == "riffle-e-31137" and integer(p.get("minor"), 0, 65535)
                and integer(p.get("fw"), 0, 4294967295)
                and integer(p.get("stream_hz"), 1, 50)
                and p.get("inputs") == ["accel_raw", "gyro_raw", "reel_counts"]):
            return "caps", {key: p[key] for key in CAP_KEYS}
        flags = [p.get(k) for k in ("accel_ok", "gyro_ok")]
        field, reel = p.get("field"), p.get("reel_counts")
        if (not integer(p.get("ms"), 0, 4294967295)
                or not all(integer(x, 0, 1) for x in flags)
                or not integer(field, 0, 4)
                or not (integer(reel, 0, 4095) if field == 4 else integer(reel, -1, -1))):
            return None, None
        sample = {"api": 1, "ms": p["ms"], "field": field,
                  "reel_counts": reel if field == 4 else None}
        for stem, ok, physical in (("accel", flags[0], "accel_g"), ("gyro", flags[1], "gyro_dps")):
            raw = stem + "_raw"
            if ok and not (vector(p.get(raw), True) and vector(p.get(physical), False)):
                return None, None
            sample[stem + "_ok"] = bool(ok)
            sample[raw] = p[raw] if ok else None
            sample[physical] = p[physical] if ok else None
        sample.update(dict.fromkeys(UNAVAILABLE))
        return "sample", sample
    except (ValueError, OverflowError, RecursionError):
        return None, None


class LFFramer:
    """Preserve split reads and discard an oversized line through its LF."""
    def __init__(self, serial):
        self.serial = serial
        self.partial = bytearray()
        self.discard = False
        self.pending = deque()

    def receive(self, wanted, deadline):
        while time.monotonic() < deadline:
            if not self.pending:
                self.feed(self.serial.read_until(b"\n", 1025))
            while self.pending:
                kind, data = classify(self.pending.popleft())
                if kind == wanted:
                    return data
        return None

    def feed(self, chunk):
        for byte in chunk:
            if self.discard:
                if byte == 10:
                    self.discard = False
                continue
            self.partial.append(byte)
            if len(self.partial) > 1024:
                self.partial.clear()
                self.discard = byte != 10
            elif byte == 10:
                self.pending.append(bytes(self.partial))
                self.partial.clear()


def capture(serial, seconds, write):
    """Caller owns the open serial port. No user- or file-supplied commands."""
    start = time.monotonic()
    seq = 0
    frames = LFFramer(serial)

    def record(kind, **data):
        nonlocal seq
        write({"schema": 1, "source": "LIVE", "seq": seq,
               "offset_ms": int((time.monotonic() - start) * 1000), "kind": kind, **data})
        seq += 1

    status, count, off = "incomplete", 0, None
    commanded_stream = False
    try:
        serial.write(COMMANDS[0])
        caps = frames.receive("caps", time.monotonic() + 3)
        if caps is None:
            raise RuntimeError("No valid Pocket Reel API v1 caps on the selected COM port")
        record("caps", data=caps)
        if seconds is None:
            serial.write(COMMANDS[1])
            sample = frames.receive("sample", time.monotonic() + 3)
            if sample is None:
                raise RuntimeError("No valid diagnostic sample received")
            record("sample", data=sample)
            count = 1
        else:
            # Mark attempted before writing, so a partial failure still tries cleanup.
            commanded_stream = True
            serial.write(COMMANDS[2])
            if frames.receive("ack", time.monotonic() + 3) is not True:
                raise RuntimeError("Stream start was not acknowledged")
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                sample = frames.receive("sample", end)
                if sample is None:
                    break
                record("sample", data=sample)
                count += 1
            if not count:
                raise RuntimeError("Stream delivered no valid samples")
        status = "complete"
    finally:
        if commanded_stream:
            try:
                serial.write(COMMANDS[3])
                off = frames.receive("ack", time.monotonic() + 2) is True
            except (OSError, RuntimeError):
                off = False
            if not off:
                status = "incomplete"
        record("end", status=status, samples=count, stream_off_confirmed=off)
    if status != "complete":
        raise RuntimeError("Stream stop unconfirmed; reconnect or restart device before another capture")


def replay(stream, output=None, observe=None):
    """Emit only known diagnostic fields; never open a COM port."""
    source, seq, offset, count, complete = None, 0, 0, 0, False
    ended, has_caps = False, False
    while True:
        line = stream.readline(4097)
        if line == "":
            break
        if len(line) > 4096:
            raise ValueError("Oversized timeline row")
        if not line.endswith("\n"):
            raise ValueError("Timeline row is missing its LF terminator")
        p = json.loads(line, object_pairs_hook=json_object)
        if (not isinstance(p, dict) or not integer(p.get("schema"), 1, 1)
                or not integer(p.get("seq"), seq, seq)
                or not integer(p.get("offset_ms"), offset, 4294967295) or ended
                or p.get("source") not in ("LIVE", "SYNTHETIC")):
            raise ValueError("Bad timeline schema, order, or source")
        source = p["source"] if source is None else source
        if p["source"] != source:
            raise ValueError("Mixed live and synthetic records")
        kind = p.get("kind")
        row = {k: p[k] for k in ("schema", "seq", "offset_ms", "source", "kind")}
        row["mode"] = "REPLAY"
        if (kind == "caps" and seq == 0) or (kind == "sample" and has_caps):
            data = p.get("data")
            if not isinstance(data, dict):
                raise ValueError("Invalid diagnostic data")
            wire = dict(data)
            if kind == "sample":
                for key in ("accel_ok", "gyro_ok"):
                    if type(data.get(key)) is not bool:
                        raise ValueError("Invalid sample validity flag")
                    wire[key] = int(data[key])
                if data.get("reel_counts") is None:
                    wire["reel_counts"] = -1
            parsed_kind, normalized = classify(
                json.dumps(wire, separators=(",", ":")).encode("ascii") + b"\n")
            if parsed_kind != kind:
                raise ValueError("Invalid diagnostic payload")
            row["data"] = normalized
            has_caps = True
            count += int(kind == "sample")
        elif kind == "end":
            status, off = p.get("status"), p.get("stream_off_confirmed")
            if (not integer(p.get("samples"), count, count) or status not in ("complete", "incomplete")
                    or (off is not None and type(off) is not bool)
                    or (status == "complete" and (not count or off is False))):
                raise ValueError("Bad end marker")
            complete = status == "complete"
            ended = True
            row.update(status=status, samples=count, stream_off_confirmed=off)
        else:
            raise ValueError("Unexpected timeline row")
        offset = p["offset_ms"]
        if observe is not None:
            observe(row)
        if output is not None:
            print(json.dumps(row, separators=(",", ":"), allow_nan=False), file=output)
        seq += 1
    return complete


def validate(stream):
    """Validate the same offline schema without emitting individual readings."""
    report = {"source": None, "samples": 0, "reel_valid": 0, "gyro_valid": 0}

    def observe(row):
        report["source"] = row["source"]
        if row["kind"] == "sample":
            report["samples"] += 1
            report["reel_valid"] += int(row["data"]["reel_counts"] is not None)
            report["gyro_valid"] += int(row["data"]["gyro_ok"])

    report["complete"] = replay(stream, observe=observe)
    return report


def capture_windows(port_name, output, seconds):
    if sys.platform != "win32" or not re.fullmatch(r"COM[1-9][0-9]{0,3}", port_name.upper()):
        raise ValueError("Capture requires Windows and an explicit COM1–COM9999 port")
    if seconds is not None and not integer(seconds, 1, 120):
        raise ValueError("Stream duration must be 1–120 seconds")
    import serial
    from serial.tools import list_ports
    name = port_name.upper()
    if name not in {x.device.upper() for x in list_ports.comports()}:
        raise ValueError("Selected Windows COM port is not enumerated")
    with output.open("x", encoding="utf-8", newline="\n") as f:
        dev = serial.Serial(port=None, baudrate=115200, bytesize=8, parity="N", stopbits=1,
                            xonxoff=False, rtscts=False, dsrdtr=False, timeout=.2, write_timeout=.5)
        dev.port = name
        dev.dtr = dev.rts = False
        try:
            dev.open()
            def write(row):
                f.write(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n")
                f.flush()
            capture(dev, seconds, write)
        finally:
            dev.close()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cmd = cli.add_subparsers(dest="mode", required=True)
    cap = cmd.add_parser("capture", help="Read from an explicitly chosen Windows COM port")
    cap.add_argument("--port", required=True)
    cap.add_argument("--output", type=Path, required=True)
    cap.add_argument("--seconds", type=int, help="Explicit bounded stream; default is one sample")
    play = cmd.add_parser("replay", help="Emit diagnostic records only; no serial or gameplay injection")
    play.add_argument("trace", type=Path)
    check = cmd.add_parser("validate", help="Validate offline trace and print counts only")
    check.add_argument("trace", type=Path)
    args = cli.parse_args()
    try:
        if args.mode == "replay":
            with args.trace.open(encoding="utf-8", newline="") as f:
                if not replay(f, sys.stdout):
                    raise RuntimeError("Timeline is incomplete or has no samples")
        elif args.mode == "validate":
            with args.trace.open(encoding="utf-8", newline="") as f:
                report = validate(f)
            print(json.dumps(report, separators=(",", ":"), allow_nan=False))
            if not report["complete"]:
                raise RuntimeError("Timeline is incomplete or has no samples")
        else:
            capture_windows(args.port, args.output, args.seconds)
    except (ValueError, RuntimeError, ImportError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
