from pydantic import BaseModel, ConfigDict
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
    project_id: Union[str, int]
    project_name: Optional[str] = "Unknown Project"
    id: Optional[Union[str, int]] = None
    name: Optional[str] = None
    work_order_number: Optional[str] = None
    client_name: Optional[str] = None
    project_code: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
