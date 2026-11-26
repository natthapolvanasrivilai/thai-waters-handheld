"""Rebuild the one changed viewer part using the installed-to-print registration."""
from pathlib import Path
import sys
import json
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0,str(ROOT/"docs/handbook/pcb-assembly"))
from build_scene import Scene
source = HERE/"Print/power-cap.stl"
poses = HERE.with_name("TW-A-0001-R0011")/"part-orientations.json"
pose = np.linalg.inv(json.loads(poses.read_bytes())["power-cap"]["assembly_to_print"])
scene = Scene()
scene.add("cap",trimesh.load_mesh(source),source,pose,.003)
(HERE/"QA/viewer-cap.json").write_text(json.dumps(scene.parts["cap"],separators=(",",":"))+"\n")
