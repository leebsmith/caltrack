#!/usr/bin/env python3
"""
caltrack.domains.tracker
Pure‑logic CRUD for food, activity, and fluid entries.
The CLI handles persistence via caltrack.storage.journal.append_record.
"""
from datetime import date
from typing import Dict, Any, List

# ---------------------------------------------------------------------
# Creation helpers (return dicts – caller is responsible for persistence)
# ---------------------------------------------------------------------

def _base_rec(id: str, d: date, typ: str, desc: str) -> Dict[str, Any]:
    return {
        "id": id,
        "date": d.isoformat(),
        "type": typ,
        "description": desc,
    }


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
# The following list/update/delete functions REQUIRE persistence layer.
# They will be implemented after storage.journal helpers are finalised.
# ---------------------------------------------------------------------


def list_entries(start: date | None = None, end: date | None = None) -> List[Dict[str, Any]]:
    raise NotImplementedError("Persistence layer not wired yet – CLI will call storage directly.")


def update_entry(id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    raise NotImplementedError


def delete_entry(id: str):
    raise NotImplementedError
