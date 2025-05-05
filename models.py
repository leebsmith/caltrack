from datetime import date
from typing import Literal, Optional, Union, List, Dict
from pydantic import BaseModel

# Define specific entry types

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

class WeightEntry(BaseModel):
    id: str
    date: date
    kg: float

Entry = Union[FoodEntry, ActivityEntry, FluidEntry, WeightEntry]

# Define target and range

class Target(BaseModel):
    id: Optional[str]
    date: Optional[str]
    contains: Optional[str]
    type: Optional[Literal["food", "activity", "fluid", "weight"]]

class Range(BaseModel):
    type: Literal["relative", "absolute"]
    value: str

# Define allowed actions explicitly

AllowedAction = Literal[
    "add", "add_weight",
    "read", "read_weight",
    "update", "update_weight",
    "delete", "delete_weight"
]

# Command model

class Command(BaseModel):
    action: AllowedAction
    target: Optional[Target] = None
    entries: Optional[List[Entry]] = None
    needs_confirmation: Optional[bool] = False
    range: Optional[Range] = None
    format: Optional[Literal["daily", "ma3", "ma5", "ma7"]] = None
    set: Optional[Dict[str, Union[str, int, float]]] = None
    explicit_time: bool = False
