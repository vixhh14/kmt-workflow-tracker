from pydantic import BaseModel, Field, field_serializer, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

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
    project_name: str
    client_name: Optional[str] = None
    project_code: Optional[str] = None
    created_at: Optional[str] = None
    is_deleted: bool = False

    @field_serializer('project_id')
    def serialize_id(self, v, _info):
        return str(v) if v else ""
    
    @field_serializer('created_at')
    def serialize_datetime(self, dt, _info):
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt or "")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
