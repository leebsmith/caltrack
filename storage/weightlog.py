import os
import json
from pathlib import Path
from datetime import datetime

WEIGHT_FILE = Path.home() / ".caltrack" / "weights.ndjson"

def ensure_dir():
    WEIGHT_FILE.parent.mkdir(parents=True, exist_ok=True)

def read_all() -> list[dict]:
    ensure_dir()
    out = []
    # open in a+ so file is created if missing
    with WEIGHT_FILE.open("a+") as f:
        f.seek(0)                         # <-- reset to start for reading
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out

def write_all(records: list[dict]) -> None:
    ensure_dir()
    tmp = WEIGHT_FILE.with_suffix(".tmp")
    with tmp.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())             # ensure it's on disk
    tmp.replace(WEIGHT_FILE)
