from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ProjectCreate(BaseModel):
    project_name: str
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: str

class ProjectOut(BaseModel):
    project_id: int
    project_name: str
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: str
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
