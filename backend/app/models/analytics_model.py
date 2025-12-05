from pydantic import BaseModel
from typing import List, Dict, Any

class AnalyticsData(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    tasks_by_priority: Dict[str, int]
    tasks_by_status: Dict[str, int]
    machine_usage: Dict[str, int] # Machine ID -> Task count
    revenue_estimated: float

class DateRange(BaseModel):
    start_date: str
    end_date: str
