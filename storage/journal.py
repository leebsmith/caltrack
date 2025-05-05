import json
from pathlib import Path

JOURNAL = Path.home() / ".caltrack" / "entries.ndjson"

def append_record(rec: dict):
    allowed_types = ('food', 'activity', 'fluid', 'weight')
    if rec['type'] not in allowed_types:
        raise ValueError(f"Unknown record type: {rec['type']}")
    JOURNAL.parent.mkdir(exist_ok=True)
    with JOURNAL.open("a") as f:
        f.write(json.dumps(rec) + "\n")

def read_all_records():
    records = []
    if not JOURNAL.exists():
        return records
    with JOURNAL.open("r") as f:
        for line in f:
            records.append(json.loads(line.strip()))
    return records

def _rewrite_all_records(records):
    JOURNAL.parent.mkdir(exist_ok=True)
    with JOURNAL.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
