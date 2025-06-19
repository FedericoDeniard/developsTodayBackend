from pydantic import BaseModel, Field, validator
from typing import Union, List, Optional, Dict, Any
from enum import Enum

# Import from models module
from models.models import Cat, Mission, Target, Note, StatusType

class CatCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Cat name")
    years_of_experience: int = Field(..., ge=0, le=50, description="Years of experience (0-50)")
    breed: str = Field(..., min_length=1, max_length=100, description="Cat breed")
    salary: int = Field(..., gt=0, description="Salary must be positive")

class CatResponse(BaseModel):
    id: int
    name: str
    years_of_experience: int
    breed: str
    salary: int

class TargetCreate(BaseModel):
    status: StatusType
    name: str = Field(..., min_length=1, max_length=255, description="Target name")
    country: str = Field(..., min_length=1, max_length=100, description="Target country")

class MissionCreate(BaseModel):
    assigned_cat: Union[int, None] = Field(None, gt=0, description="Cat ID if assigning")
    status: StatusType
    title: str = Field(..., min_length=1, max_length=255, description="Mission title")
    targets: List[TargetCreate] = Field(..., min_items=1, max_items=3, description="1-3 targets required")

class MissionResponse(BaseModel):
    id: int
    assigned_cat: Union[int, None]
    status: str
    title: str

class TargetResponse(BaseModel):
    id: int
    assigned_mission: int
    status: str
    name: str
    country: str

class NoteCreate(BaseModel):
    target_id: int = Field(..., gt=0, description="Target ID")
    message: str = Field(..., min_length=1, max_length=1000, description="Note message")

class NoteResponse(BaseModel):
    id: int
    target_id: int
    message: str

class SalaryUpdate(BaseModel):
    salary: int = Field(..., gt=0, description="New salary must be positive")

class StatusUpdate(BaseModel):
    status: StatusType

class CatAssignment(BaseModel):
    cat_id: int = Field(..., gt=0, description="Cat ID to assign")


#

class StatusType(Enum):
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

class Target(BaseModel):
    assigned_mission: int
    status: StatusType
    name: str
    country: str

class Note(BaseModel):
    target_id: int
    message: str
