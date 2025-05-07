import uuid
from datetime import datetime
from typing import Dict, Any, List
from caltrack.storage.journal import append_record, read_all_records, _rewrite_all_records

def _base_rec(id: str, ts: datetime, kg: float) -> Dict[str, Any]:
    return {
        "id": id,
        "type": "weight",
        "ts": ts.isoformat(),
        "kg": kg
    }

def add(ts: datetime, kg: float) -> Dict[str, Any]:
    rec = _base_rec(uuid.uuid4().hex[:8], ts, kg)
    append_record(rec)
    return rec

def list_weights() -> List[Dict[str, Any]]:
    records = read_all_records()
    weights = [r for r in records if r.get('type') == 'weight']
    print(f"DEBUG: Found {len(weights)} weight records")
    return weights

def update(entry_id: str, kg: float) -> Dict[str, Any]:
    records = read_all_records()
    updated = None
    for r in records:
        if r.get('id') == entry_id and r.get('type') == 'weight':
            r['kg'] = kg
            updated = r
            break
    if updated:
        _rewrite_all_records(records)
        print(f"DEBUG: Updated weight entry {entry_id}")
        return updated
    else:
        raise KeyError(f"Weight entry {entry_id} not found")

def delete(entry_id: str):
    records = read_all_records()
    new_records = [r for r in records if not (r.get('id') == entry_id and r.get('type') == 'weight')]
    if len(new_records) == len(records):
        raise KeyError(f"Weight entry {entry_id} not found")
    _rewrite_all_records(new_records)
    print(f"DEBUG: Deleted weight entry {entry_id}")
