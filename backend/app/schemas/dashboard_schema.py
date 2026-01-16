from pydantic import BaseModel, Field, field_serializer, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class DashboardProject(BaseModel):
    # Map project_id to id for frontend
    id: str = Field(alias="id")
    name: Optional[str] = Field(default=None, alias="project_name")
    code: Optional[str] = Field(default=None, alias="project_code")
    work_order: Optional[str] = Field(default=None, alias="work_order_number")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class DashboardTask(BaseModel):
    id: str = Field(alias="task_id")
    title: str
    status: str
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class DashboardMachine(BaseModel):
    id: str = Field(alias="machine_id")
    machine_name: str
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class DashboardUser(BaseModel):
    # Map user_id to id for frontend
    id: str = Field(alias="user_id")
    username: str
    role: str
    full_name: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class DashboardOperator(BaseModel):
    # Map user_id to id for frontend
    id: str = Field(alias="user_id")
    username: str
    name: Optional[str] = Field(default=None, alias="full_name")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class DashboardOverviewCounts(BaseModel):
    total: int = 0
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    ended: int = 0
    on_hold: int = 0

class DashboardMachineOverview(BaseModel):
    active: int = 0
    total: int = 0

class DashboardProjectOverview(BaseModel):
    total: int = 0
    completed: int = 0
    in_progress: int = 0
    yet_to_start: int = 0
    held: int = 0

class DashboardOverview(BaseModel):
    tasks: DashboardOverviewCounts
    machines: DashboardMachineOverview
    projects: DashboardProjectOverview

class AdminDashboardOut(BaseModel):
    projects: List[DashboardProject]
    tasks: List[DashboardTask]
    machines: List[DashboardMachine]
    users: List[DashboardUser]
    operators: List[DashboardOperator]
    overview: DashboardOverview

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class SupervisorDashboardOut(BaseModel):
    projects: List[DashboardProject]
    tasks: List[DashboardTask]
    machines: List[DashboardMachine]
    operators: List[DashboardOperator]
    overview: DashboardOverview

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class PerformanceMetrics(BaseModel):
    total_tasks: int
    completed_tasks: int
    on_hold_tasks: int
    rescheduled_tasks: int
    avg_time_per_task_seconds: float
    total_working_duration_seconds: int
    completion_percentage: float

class GraphDataItem(BaseModel):
    date: str
    duration: int

class OperatorPerformanceOut(BaseModel):
    metrics: PerformanceMetrics
    graph_data: List[GraphDataItem]

class TaskSummaryOut(BaseModel):
    project_stats: DashboardProjectOverview
    task_stats: Dict[str, int]

class AttendanceUser(BaseModel):
    id: str
    name: str
    username: str
    role: str
    unit_id: Optional[int] = None
    status: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    login_time: Optional[str] = None

class AttendanceRecord(BaseModel):
    user_id: str
    user: str
    username: str
    role: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str
    date: str

class AttendanceSummaryOut(BaseModel):
    success: bool
    date: str
    present: int
    absent: int
    total_users: int
    present_users: List[AttendanceUser]
    absent_users: List[AttendanceUser]
    records: List[AttendanceRecord]

class OperatorHold(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None
    duration_seconds: int = 0
    reason: str = ""

class OperatorTask(BaseModel):
    id: str
    title: str
    project: str
    description: str
    part_item: str
    nos_unit: str
    status: str
    priority: str
    assigned_to: str
    machine_id: str
    machine_name: str
    assigned_by: str
    assigned_by_name: str
    due_date: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_duration_seconds: int = 0
    total_held_seconds: int = 0
    holds: List[OperatorHold] = []

class OperatorStats(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    on_hold_tasks: int

class OperatorUserInfo(BaseModel):
    user_id: str
    username: str
    full_name: Optional[str] = None

class OperatorDashboardOut(BaseModel):
    tasks: List[OperatorTask]
    stats: OperatorStats
    user: OperatorUserInfo

class ProjectAnalyticsStats(BaseModel):
    total: int
    yet_to_start: int
    in_progress: int
    completed: int
    on_hold: int

class ProjectAnalyticsChart(BaseModel):
    yet_to_start: int
    in_progress: int
    completed: int
    on_hold: int

class ProjectAnalyticsOut(BaseModel):
    project: str
    stats: ProjectAnalyticsStats
    chart: ProjectAnalyticsChart

class DailyMachineReportItem(BaseModel):
    machine_id: str
    machine_name: str
    unit: str
    category: str
    date: str
    runtime_seconds: int
    tasks_run_count: int
    is_running_now: bool
    status: str

class DailyMachineReportOut(BaseModel):
    date: str
    report: List[DailyMachineReportItem]

class DailyUserReportItem(BaseModel):
    user_id: str
    username: str
    full_name: Optional[str] = None
    role: str
    date: str
    tasks_worked_count: int
    total_work_seconds: int
    machines_used: List[str]
    status: str

class DailyUserReportOut(BaseModel):
    date: str
    report: List[DailyUserReportItem]

class MonthlyPerformanceChartItem(BaseModel):
    month: str
    tasks_completed: int
    aht: float

class MonthlyPerformanceCSVRow(BaseModel):
    month: str
    tasks_completed: int
    total_runtime_hms: str
    total_runtime_seconds: int
    aht_hms: str
    aht_seconds: int

class MonthlyPerformanceOut(BaseModel):
    year: int
    chart_data: List[MonthlyPerformanceChartItem]
    csv_rows: List[MonthlyPerformanceCSVRow]

class DetailedMachineActivityItem(BaseModel):
    task_id: str
    task_title: str
    operator: str
    start_time: str
    end_time: Optional[str] = None
    runtime_seconds: int

    held_time_seconds: int
    status: str

class DetailedHold(BaseModel):
    start: str
    end: Optional[str] = None
    reason: Optional[str] = None
    duration_seconds: int

class DetailedUserActivityItem(BaseModel):
    task_id: str
    task_title: str
    machine_name: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: int

    holds: List[DetailedHold]
    status: str
