import json
from pathlib import Path

JOURNAL = Path.home() / ".caltrack" / "entries.ndjson"

def append_record(rec: dict):
    JOURNAL.parent.mkdir(exist_ok=True)
    with JOURNAL.open("a") as f:
        f.write(json.dumps(rec) + "\n")
