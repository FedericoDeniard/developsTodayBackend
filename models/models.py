from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Union

class StatusType(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class Cat(BaseModel):
    name: str
    years_of_experience: int
    breed: str
    salary: int

class Mission(BaseModel):
    assigned_cat: Optional[int] = None
    status: StatusType
    title: str
    targets: List['Target'] = []

class Target(BaseModel):
    assigned_mission: int
    status: StatusType
    name: str
    country: str

class Note(BaseModel):
    target_id: int
    message: str
