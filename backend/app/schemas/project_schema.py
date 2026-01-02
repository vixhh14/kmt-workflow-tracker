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
    # Map database project_id to frontend id
    id: UUID = Field(alias="project_id")
    project_name: str = "Unknown Project"
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: Optional[str] = None
    created_at: Optional[datetime] = None

    @field_serializer('id')
    def serialize_uuid(self, v: UUID, _info):
        """Serialize UUID to string for JSON response"""
        return str(v) if v else None
    
    @field_serializer('created_at')
    def serialize_datetime(self, dt: Optional[datetime], _info):
        """Serialize datetime to ISO 8601 string"""
        if isinstance(dt, datetime):
            return dt.isoformat()
        return dt

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
