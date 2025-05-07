from datetime import date
from typing import Literal, Optional, Union, List, Dict
from pydantic import BaseModel

# --- Entry Types ---

class FoodEntry(BaseModel):
    id: str
    date: date
    meal: Literal[
        "breakfast", "brunch", "lunch", "afternoon snack",
        "dinner", "late snack", "late night snack"
    ]
    description: str
    kcal: int

class ActivityEntry(BaseModel):
    id: str
    date: date
    description: str
    kcal_burned: int  # Should be negative for calories burned

class FluidEntry(BaseModel):
    id: str
    date: date
    description: str
    volume_ml: int

class WeightEntry(BaseModel):
    id: str
    date: date
    kg: float

Entry = Union[FoodEntry, ActivityEntry, FluidEntry, WeightEntry]

# --- Target + Range ---


class Target(BaseModel):
    id: Optional[str] = None
    date: Optional[str] = None
    contains: Optional[str] = None
    type: Optional[Literal["food", "activity", "fluid", "weight"]] = None


class Range(BaseModel):
    type: Literal["relative", "absolute"]
    value: str  # e.g., "2023-04-01 to 2023-04-30"

# --- Allowed Actions ---

AllowedAction = Literal[
    "add", "add_weight",
    "read", "read_weight",
    "update", "update_weight",
    "delete", "delete_weight"
]

# --- Command Schema ---

class Command(BaseModel):
    action: AllowedAction
    target: Optional[Target] = None  # Required for read/delete; may omit date if type is set
    entries: Optional[List[Entry]] = None
    needs_confirmation: Optional[bool] = False
    range: Optional[Range] = None
    format: Optional[Literal["daily", "ma3", "ma5", "ma7"]] = None
    set: Optional[Dict[str, Union[str, int, float]]] = None
    explicit_time: bool = False
