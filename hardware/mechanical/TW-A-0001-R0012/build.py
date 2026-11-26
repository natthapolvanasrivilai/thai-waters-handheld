from pathlib import Path
import json
import hashlib

HERE = Path(__file__).resolve().parent
OLD = HERE.with_name("TW-A-0001-R0011")
LEGACY = HERE.with_name("TW-A-0001-R0010")

def digest(path):
    return hashlib.file_digest(path.open("rb"),"sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_text(encoding="utf8"))

def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf8")
