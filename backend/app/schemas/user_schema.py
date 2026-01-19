from pydantic import BaseModel, Field, field_serializer, ConfigDict
from typing import Optional, Union
from datetime import datetime

class UserBase(BaseModel):
    username: str
    role: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str   # Only for input, hashed before write

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

class UserOut(UserBase):
    user_id: str
    id: str # Alias for user_id
    active: bool = True
    created_at: Optional[Union[datetime, str]] = None
    password_hash: Optional[str] = None

    @field_serializer('created_at')
    def serialize_dt(self, dt: Optional[Union[datetime, str]], _info):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
