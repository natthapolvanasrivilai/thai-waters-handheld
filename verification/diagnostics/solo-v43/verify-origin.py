"""Allow exactly the prior successful already-public V43 artifact; no extraction."""
import argparse
import hashlib
import json
from pathlib import Path

OWNER_REPO = "natthapolvanasrivilai/thai-waters-handheld"
REPO_ID = 1462766665
SOURCE = "0ba72cf4c55f141fbd0f692a7e2bf8cfb83ba984"
RUN = 44944834035
ARTIFACT = 14723860188
SHA = "a01b2f7d2cd7a5bacacd08ba8ed2d0fb2f0a14e11cd4458bcd8ac868c7681344"
SIZE = 4649841

def verify(artifact, run, archive):
    valid = (
        artifact.get("id") == ARTIFACT
        and artifact.get("name") == f"browser-{SOURCE}"
        and artifact.get("expired") is False
        and artifact.get("size_in_bytes") == SIZE
        and artifact.get("digest") == f"sha256:{SHA}"
        and artifact.get("workflow_run") == {
            "id": RUN, "repository_id": REPO_ID, "head_repository_id": REPO_ID,
            "head_branch": "main", "head_sha": SOURCE,
        }
        and run.get("id") == RUN
        and run.get("run_attempt") == 1
        and run.get("head_sha") == SOURCE
        and run.get("head_branch") == "main"
        and run.get("event") == "push"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and run.get("repository", {}).get("full_name") == OWNER_REPO
        and run.get("repository", {}).get("id") == REPO_ID
        and run.get("path") == ".github/workflows/verify-release-artifacts.yml"
        and archive.stat().st_size == SIZE
    )
    return valid and hashlib.sha256(archive.read_bytes()).hexdigest() == SHA

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact_metadata", type=Path)
    p.add_argument("run_metadata", type=Path)
    p.add_argument("archive", type=Path)
    a = p.parse_args()
    try:
        valid = verify(json.loads(a.artifact_metadata.read_text()), json.loads(a.run_metadata.read_text()), a.archive)
    except (TypeError, ValueError, OSError, AttributeError):
        valid = False
    if not valid:
        p.exit(1, "V43 pinned archive identity rejected.\n")
    print("Verified immutable successful V43 artifact, metadata, size and SHA.")

if __name__ == "__main__":
    main()
