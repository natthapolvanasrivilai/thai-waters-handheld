"""Reopen the editable input in a separate local Bambu Studio process for each check."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess

from make_project import PARENT, PROJECT


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("slicer", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    for name, project, plate in [("baseline", PARENT, 1), ("all", PROJECT, 0), ("reopen", PROJECT, 1)]:
        folder = (args.scratch/name).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        if (folder/"result.json").exists():
            raise FileExistsError(f"Use a fresh output folder for {name}: {folder}")
        with (folder/"native.log").open("wb") as log:
            subprocess.run([str(args.slicer.resolve()), "--slice", str(plate), "--outputdir", str(folder),
                            "--export-3mf", "sliced.3mf", str(project)], check=True, cwd=folder,
                           stdout=log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        print(name, "sliced", flush=True)
