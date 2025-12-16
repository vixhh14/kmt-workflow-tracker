from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OutsourceBase(BaseModel):
    task_id: Optional[int] = None
    title: str
    vendor: str
    description: Optional[str] = None
    dc_generated: bool = False
    transport_status: str = "pending"  # pending, in_transit, delivered
    follow_up_time: Optional[datetime] = None
    pickup_status: str = "pending"  # pending, scheduled, picked_up
    status: str = "pending"  # pending, received
    cost: float = 0.0
    expected_date: Optional[str] = None

class OutsourceCreate(OutsourceBase):
    pass

class OutsourceUpdate(BaseModel):
    task_id: Optional[int] = None
    title: Optional[str] = None
    vendor: Optional[str] = None
    description: Optional[str] = None
    dc_generated: Optional[bool] = None
    transport_status: Optional[str] = None
    follow_up_time: Optional[datetime] = None
    pickup_status: Optional[str] = None
    status: Optional[str] = None
    cost: Optional[float] = None
    expected_date: Optional[str] = None

class Outsource(OutsourceBase):
    id: str
    updated_at: datetime

    class Config:
        from_attributes = True
