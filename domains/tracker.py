#!/usr/bin/env python3
"""
caltrack.domains.tracker
Pure‑logic CRUD for food, activity, and fluid entries **with** persistence.

* The CLI handles **ADD** by calling the `add_*` helpers below and
  then writing via `storage.journal.append_record` (one‑line append).
* For READ / UPDATE / DELETE we need full persistence here so the CLI
  can call `list_entries`, `update_entry`, and `delete_entry`.

Storage format: `~/.caltrack/entries.ndjson` — one JSON object per line.
Each record has at minimum:
    id, date (ISO‑YYYY‑MM‑DD), type (food|activity|fluid), description
Plus type‑specific fields:
    food:    meal, kcal
    activity:kcal_burned
    fluid:   volume_ml
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

JOURNAL = Path.home() / ".caltrack" / "entries.ndjson"

# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _read_all() -> List[Dict[str, Any]]:
    """Return every entry dict (empty list if the file doesn’t exist)."""
    if not JOURNAL.exists():
        return []
    with JOURNAL.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_all(recs: List[Dict[str, Any]]):
    """Rewrite the NDJSON file with `recs`."""
    JOURNAL.parent.mkdir(exist_ok=True)
    with JOURNAL.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _base_rec(id: str, d: date, typ: str, desc: str) -> Dict[str, Any]:
    return {
        "id": id,
        "date": d.isoformat(),
        "type": typ,
        "description": desc,
    }

# ---------------------------------------------------------------------
# ADD helpers (return dict; caller persists with append_record)
# ---------------------------------------------------------------------

def add_food(id: str, d: date, meal: str, description: str, kcal: int) -> Dict[str, Any]:
    rec = _base_rec(id, d, "food", description)
    rec.update({"meal": meal, "kcal": kcal})
    return rec


def add_activity(id: str, d: date, description: str, kcal_burned: int) -> Dict[str, Any]:
    rec = _base_rec(id, d, "activity", description)
    rec.update({"kcal_burned": kcal_burned})
    return rec


def add_fluid(id: str, d: date, description: str, volume_ml: int) -> Dict[str, Any]:
    rec = _base_rec(id, d, "fluid", description)
    rec.update({"volume_ml": volume_ml})
    return rec

# ---------------------------------------------------------------------
# READ / UPDATE / DELETE with persistence
# ---------------------------------------------------------------------

def list_entries(start: date | None = None, end: date | None = None) -> List[Dict[str, Any]]:
    """Return entries whose `date` is between *start* and *end* inclusive."""
    recs = _read_all()
    if start is None and end is None:
        return recs
    if start is None:
        start = date.min
    if end is None:
        end = date.max
    rng: List[Dict[str, Any]] = []
    for r in recs:
        try:
            d = date.fromisoformat(r["date"])
        except (ValueError, KeyError):
            # skip malformed dates
            continue
        if start <= d <= end:
            rng.append(r)
    return rng


def update_entry(id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    """Update a record in‑place and return the modified dict.

    *changes* may contain any writable key: description, kcal, etc.
    If *id* is not found, KeyError is raised.
    """
    recs = _read_all()
    for r in recs:
        if r.get("id") == id:
            r.update(changes)
            updated = r
            break
    else:
        raise KeyError(f"No tracker record with id={id}")
    _write_all(recs)
    return updated


def delete_entry(id: str):
    """Delete the record whose id matches *id*. Raises KeyError if absent."""
    recs = _read_all()
    new_recs = [r for r in recs if r.get("id") != id]
    if len(new_recs) == len(recs):
        raise KeyError(f"No tracker record with id={id}")
    _write_all(new_recs)
