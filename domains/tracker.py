import uuid
from datetime import date
from typing import Dict, Any, List
from caltrack.storage.journal import append_record, read_all_records, _rewrite_all_records

def _base_rec(id: str, d: date, type_: str, description: str) -> Dict[str, Any]:
    return {
        "id": id,
        "date": d.isoformat(),
        "type": type_,
        "description": description
    }

def add_food(id: str, d: date, meal: str, description: str, kcal: int) -> Dict[str, Any]:
    rec = _base_rec(id, d, "food", description)
    rec.update({"meal": meal, "kcal": kcal})
    append_record(rec)
    return rec

def add_activity(id: str, d: date, description: str, kcal_burned: int) -> Dict[str, Any]:
    rec = _base_rec(id, d, "activity", description)
    rec.update({"kcal_burned": kcal_burned})
    append_record(rec)
    return rec

def add_fluid(id: str, d: date, description: str, volume_ml: int) -> Dict[str, Any]:
    rec = _base_rec(id, d, "fluid", description)
    rec.update({"volume_ml": volume_ml})
    append_record(rec)
    return rec

def list_entries() -> List[Dict[str, Any]]:
    records = read_all_records()  # <-- Always fresh read from file
    return [r for r in records if r.get('type') in ('food', 'activity', 'fluid')]

def update_entry(entry_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    records = read_all_records()
    updated = None
    for r in records:
        if r.get('id') == entry_id:
            r.update(changes)
            updated = r
            break
    if updated:
        _rewrite_all_records(records)
        return updated
    else:
        raise KeyError(f"Entry {entry_id} not found")

def delete_entry(entry_id: str):
    records = read_all_records()
    new_records = [r for r in records if r.get('id') != entry_id]
    if len(new_records) == len(records):
        raise KeyError(f"Entry {entry_id} not found")
    _rewrite_all_records(new_records)
