from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    role: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    machine_types: Optional[str] = None

class UserCreate(UserBase):
    password: str   # Only for creation

class UserUpdate(BaseModel):
    role: Optional[str] = None
    full_name: Optional[str] = None
    machine_types: Optional[str] = None
    unit_id: Optional[int] = None

class UserOut(UserBase):
    user_id: str
    machine_types: Optional[str] = None
    updated_at: Optional[datetime] = None
    id: Optional[str] = None
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
