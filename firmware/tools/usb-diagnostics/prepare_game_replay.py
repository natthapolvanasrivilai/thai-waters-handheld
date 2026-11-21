"""Validate one complete API1 JSONL capture for the offline native replay witness."""

import sys

from usb_diagnostics import replay

MAX_SAMPLES = 4096


def prepare(stream, output):
    rows = []
    source = None

    def observe(row):
        nonlocal source
        if row["kind"] == "caps":
            source = row["source"]
        elif row["kind"] == "sample":
            if len(rows) >= MAX_SAMPLES:
                raise ValueError("Trace exceeds the offline replay sample limit")
            data = row["data"]
            raw = data["reel_counts"]
            rows.append((data["ms"], -1 if raw is None else raw))

    if not replay(stream, observe=observe) or not rows:
        raise ValueError("Offline replay requires a complete trace with samples")
    # No rows leave the validator before the end marker and all preceding rows pass.
    print("TW-REEL-REPLAY-1", source, len(rows), file=output)
    for milliseconds, count in rows:
        print(milliseconds, count, file=output)


if __name__ == "__main__":
    try:
        prepare(sys.stdin, sys.stdout)
    except (ValueError, UnicodeError, OSError):
        print("Offline replay stopped: invalid, incomplete or unreadable API1 trace.",
              file=sys.stderr)
        sys.exit(1)
