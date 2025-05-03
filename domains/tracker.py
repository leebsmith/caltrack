#!/usr/bin/env python3
"""
Tracker domain: pure‑logic CRUD for meals, activities, and fluids.
Stubbed implementations to satisfy CLI imports; fill in storage logic later.
"""
from datetime import datetime
from typing import Optional, Dict, Any

# Example entry record format (we'll persist via storage.journal when ready)
# {
#   "id": "20250502-abc123",
#   "ts": "2025-05-02T19:23:00-04:00",
#   "type": "food",  # food|activity|fluid
#   "description": "2 scrambled eggs",
#   "kcal": 180,
#   "volume_ml": None,
#   "minutes": None,
#   "met": None,
# }


def add_food(id: str, date: date, meal: str,
             description: str, kcal: int) -> Dict[str, Any]:    
    """
    Stub: Log a food entry.
    Returns a dict mimicking the created record.
    Replace with actual storage.journal.append logic later.
    """
    return {
        "id": id,
        "date": date.isoformat(),
        "meal": meal,
        "description": description,
        "kcal": kcal
    }

    # TODO: append rec to entries.ndjson via storage.journal
    return rec


def add_activity(id: str, date: date,
                 description: str, kcal_burned: int) -> Dict[str, Any]:
    """
    Stub: Log an activity entry.
    Returns a dict mimicking the created record.
    """
    return {
        "id": id,
        "date": date.isoformat(),
        "description": description,
        "kcal_burned": kcal_burned
    }
    # TODO: append rec to entries.ndjson via storage.journal
    return rec


def add_fluid(id: str, date: date,
              description: str, volume_ml: int) -> Dict[str, Any]:
    """
    Stub: Log a fluid intake.
    Returns a dict mimicking the created record.
    """
    return {
        "id": id,
        "date": date.isoformat(),
        "description": description,
        "volume_ml": volume_ml
    }
    # TODO: append rec to entries.ndjson via storage.journal
    return rec
