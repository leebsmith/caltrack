from datetime import date
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

class FoodEntry(BaseModel):
    id:          str
    date:        date
    meal:        Literal[
        "breakfast", "brunch", "lunch", "afternoon snack",
        "dinner", "late snack", "late night snack"
    ]
    description: str
    kcal:        int

class ActivityEntry(BaseModel):
    id:          str
    date:        date
    description: str
    kcal_burned: int

class FluidEntry(BaseModel):
    id:          str
    date:        date
    description: str
    volume_ml:   int

class Target(BaseModel):
    id:       Optional[str]
    date:     Optional[str]
    contains: Optional[str]
    type:     Optional[str]

class Range(BaseModel):
    type:  str       # relative|absolute
    value: str       # e.g. "last month" or "2025-01-01…2025-05-01"

class Command(BaseModel):
    action:         str
    target:         Optional[Target]
    entries:        Optional[List[Any]]
    needs_confirmation: Optional[bool] = False
    range:          Optional[Range]
    format:         Optional[str]
    set:            Optional[Dict[str, Any]]
    explicit_time:  bool = False
