from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional, Union
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
    updated_at: Optional[Union[datetime, str]] = None
    id: Optional[str] = None
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('updated_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    @field_serializer('user_id', 'id')
    def serialize_id(self, v, _info):
        if v is None:
            return None
        return str(v)
