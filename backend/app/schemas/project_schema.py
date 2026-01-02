from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional, Union
from datetime import datetime

class ProjectCreate(BaseModel):
    project_name: str
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: str

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: Optional[str] = None

class ProjectOut(BaseModel):
    project_id: str
    project_name: Optional[str] = "Unknown Project"
    id: Optional[str] = None
    name: Optional[str] = None
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: Optional[str] = None
    created_at: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.isoformat()

    @field_serializer('project_id', 'id')
    def serialize_id(self, v, _info):
        if v is None:
            return None
        return str(v)
