"""Classify an exact GitHub tag-ref GET conservatively. No write operations."""
import argparse
import json
import re
import subprocess
import sys

def classify(response, returncode):
    status = re.match(rb"^HTTP/\S+\s+(\d{3})(?:\s|$)", response)
    if status and status[1] == b"404" and returncode == 1:
        return "missing"
    if status and status[1] == b"200" and returncode == 0:
        return "exists"
    raise ValueError("Could not determine tag absence from an authoritative GitHub GET")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repository")
    p.add_argument("tag")
    a = p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", a.repository):
        p.error("Invalid repository")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", a.tag):
        p.error("Invalid tag")
    if subprocess.run(["git", "check-ref-format", f"refs/tags/{a.tag}"]).returncode:
        p.error("Invalid tag")
    r = subprocess.run(["gh", "api", "--include",
                        f"repos/{a.repository}/git/ref/tags/{a.tag}"], capture_output=True)
    try:
        print(json.dumps(dict(tag_name=a.tag, status=classify(r.stdout, r.returncode))))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
