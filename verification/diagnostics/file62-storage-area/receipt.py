"""Print only finite diagnostic values. Never emit original input or exceptions."""
import json
import sys
from pathlib import Path

PREFIX = "Map standalone reload "


def summarize(record):
    allowed_lanes = {"desktop keyboard": "desktop", "mobile touch": "touch"}
    lane = record.get("lane")
    if not isinstance(lane, str) or lane not in allowed_lanes:
        return None
    info = {"lane": allowed_lanes[lane], "startupFailed": record.get("startupError") is not None}
    for key in ("sameFile", "lock", "powered", "recovery"):
        value = record.get(key)
        info[key] = value if type(value) is bool else None
    area = record.get("storageArea")
    area = area if isinstance(area, dict) else {}
    before, after, relation = (area.get(k) for k in ("beforeReported", "afterReported", "relation"))
    info["storageArea"] = {
        "beforeReported": before is True,
        "afterReported": after is True,
        "relation": relation if before is True and after is True and relation in ("same", "different") else "unknown",
    }
    for stage in ("beforeReload", "atStart", "afterBoot"):
        state = record.get(stage)
        state = state if isinstance(state, dict) else {}
        info[stage] = {key: state[key] if type(state.get(key)) is bool else None
                       for key in ("known", "present")}
        it = state.get("languageBinding")
        info[stage]["languageBinding"] = it if it in ("missing", "present", "blocked") else None
    return info


def main(path):
    count = 0
    try:
        with Path(path).open(errors="replace") as stream:
            for line in stream:
                if not line.startswith(PREFIX):
                    continue
                try:
                    record = json.loads(line[len(PREFIX):])
                except (ValueError, RecursionError):
                    continue
                info = summarize(record) if isinstance(record, dict) else None
                if info is not None:
                    print(json.dumps(info, sort_keys=True))
                    count += 1
    except OSError:
        pass
    print(f"storageAreaReceipts={count}")


if __name__ == "__main__":
    main(sys.argv[1])
