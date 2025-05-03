# caltrack/domains/weight.py

import uuid
from datetime import datetime
from caltrack.storage.weightlog import read_all, write_all

def add(ts: datetime, kg: float) -> dict:
    recs = read_all()
    new = {
        "id": uuid.uuid4().hex[:8],
        "ts": ts.isoformat(),
        "kg": kg
    }
    recs.append(new)
    write_all(recs)
    return new

def list_weights(start: datetime|None=None, end: datetime|None=None) -> list[dict]:
    recs = read_all()
    out = []
    for r in recs:
        t = datetime.fromisoformat(r["ts"])
        if (start is None or t >= start) and (end is None or t <= end):
            out.append(r)
    return out

def update(id: str, new_kg: float) -> dict:
    recs = read_all()
    for r in recs:
        if r["id"] == id:
            r["kg"] = new_kg
            r["ts"] = datetime.now().isoformat()  # update timestamp
            write_all(recs)
            return r
    raise KeyError(f"No weight record with id={id}")

def delete(id: str) -> None:
    recs = read_all()
    recs2 = [r for r in recs if r["id"] != id]
    if len(recs2) == len(recs):
        raise KeyError(f"No weight record with id={id}")
    write_all(recs2)
