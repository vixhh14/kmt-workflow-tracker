from pydantic import BaseModel, Field, field_serializer, ConfigDict
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
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    contact_number: Optional[str] = None
    machine_types: Optional[str] = None
    unit_id: Optional[str] = None
    security_question: Optional[str] = None
    security_answer: Optional[str] = None

class UserOut(UserBase):
    id: str
    machine_types: Optional[str] = None
    updated_at: Optional[datetime] = None

    @field_serializer('updated_at')
    def serialize_dt(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
