from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, case, or_
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.core.database import get_db
from app.core.time_utils import get_current_time_ist, get_today_date_ist, IST
from app.models.models_db import Task, TaskTimeLog, Machine, User, Attendance, MachineRuntimeLog, UserWorkLog, Unit, MachineCategory, Project, TaskHold
from app.utils.csv_utils import generate_csv_stream, format_duration_hms
from fastapi.responses import StreamingResponse
import io

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    responses={404: {"description": "Not found"}},
)

# ----------------------------------------------------------------------
# HELPER FUNCTIONS (Aggregation Logic)
# ----------------------------------------------------------------------

def calculate_machine_runtime(db: Session, target_date: date) -> List[dict]:
    """
    Calculate runtime for all machines on a specific date (IST) using MachineRuntimeLog.
    """
    # Fetch all machines with related info
    machines = db.query(Machine).filter(or_(Machine.is_deleted == False, Machine.is_deleted == None)).all()
    
    # Pre-fetch lookup dicts for performance (can be joined, but this is fine for low volume)
    units = {u.id: u.name for u in db.query(Unit).all()}
    categories = {c.id: c.name for c in db.query(MachineCategory).all()}
    
    machine_stats = {m.id: {"runtime": 0, "completed_tasks": 0, "is_running_now": False, "obj": m} for m in machines}
    
    # Fetch logs for the date
    logs = db.query(MachineRuntimeLog).filter(MachineRuntimeLog.date == target_date).all()
    
    now = get_current_time_ist()
    
    for log in logs:
        if log.machine_id not in machine_stats:
            continue
            
        duration = log.duration_seconds or 0
        
        # If log is currently open (running now)
        if log.end_time is None and log.date == get_today_date_ist():
            current_run = (now - log.start_time).total_seconds()
            duration = int(max(0, current_run))
            machine_stats[log.machine_id]["is_running_now"] = True
            
        machine_stats[log.machine_id]["runtime"] += duration

    # 2. Get Completed Tasks for this date
    # Fetch tasks completed within a safe window and filter in Python using IST
    tasks_query = db.query(Task).filter(
        Task.status == 'completed',
        or_(Task.is_deleted == False, Task.is_deleted == None),
        Task.actual_end_time >= datetime.combine(target_date - timedelta(days=1), datetime.min.time()),
        Task.actual_end_time <= datetime.combine(target_date + timedelta(days=1), datetime.max.time())
    ).all()
    
    completed_tasks = [t for t in tasks_query if t.actual_end_time.astimezone(IST).date() == target_date]
    
    for t in completed_tasks:
        if t.machine_id in machine_stats:
            machine_stats[t.machine_id]["completed_tasks"] += 1

    results = []
    # Sort by machine name for better readability
    sorted_machines = sorted(machine_stats.items(), key=lambda x: x[1]["obj"].machine_name)
    
    for m_id, stats in sorted_machines:
        machine = stats["obj"]
        runtime = stats["runtime"]
        results.append({
            "machine_id": machine.id,
            "machine_name": machine.machine_name,
            "unit": units.get(machine.unit_id, ""),
            "category": categories.get(machine.category_id, ""),
            "date": target_date.isoformat(),
            "runtime_seconds": runtime,
            "tasks_run_count": stats["completed_tasks"],
            "is_running_now": stats["is_running_now"],
            "status": "Active" if runtime > 0 else "Idle"
        })
        
    return results

def calculate_user_activity(db: Session, target_date: date) -> List[dict]:
    """
    Calculate user activity for a specific date (IST).
    """
    users = db.query(User).filter(
        User.role.in_(['operator', 'supervisor']),
        or_(User.is_deleted == False, User.is_deleted == None),
        User.approval_status == 'approved'
    ).all()
    # user_id -> {work_time, completed_tasks, machines}
    user_stats = {u.user_id: {"work_time": 0, "completed_tasks": 0, "obj": u, "machines": set()} for u in users}
    
    logs = db.query(UserWorkLog).filter(UserWorkLog.date == target_date).all()
    now = get_current_time_ist()
    
    for log in logs:
        if log.user_id not in user_stats:
            continue
            
        duration = log.duration_seconds or 0
        if log.end_time is None and log.date == get_today_date_ist():
            current_run = (now - log.start_time).total_seconds()
            duration = int(max(0, current_run))
            
        user_stats[log.user_id]["work_time"] += duration
        if log.machine_id:
            user_stats[log.user_id]["machines"].add(log.machine_id)
            
    # 2. Get Completed Tasks for this date
    tasks_query = db.query(Task).filter(
        Task.status == 'completed',
        or_(Task.is_deleted == False, Task.is_deleted == None),
        Task.actual_end_time >= datetime.combine(target_date - timedelta(days=1), datetime.min.time()),
        Task.actual_end_time <= datetime.combine(target_date + timedelta(days=1), datetime.max.time())
    ).all()
    
    completed_tasks = [t for t in tasks_query if t.actual_end_time.astimezone(IST).date() == target_date]
    
    for t in completed_tasks:
        if t.assigned_to in user_stats:
            user_stats[t.assigned_to]["completed_tasks"] += 1
            
    results = []
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["obj"].username)
    
    for u_id, stats in sorted_users:
        work_time = stats["work_time"]
        u_obj = stats["obj"]
        
        results.append({
            "user_id": u_obj.user_id,
            "username": u_obj.username,
            "full_name": u_obj.full_name,
            "role": u_obj.role,
            "date": target_date.isoformat(),
            "tasks_worked_count": stats["completed_tasks"],
            "total_work_seconds": work_time,
            "machines_used": list(stats["machines"]),
            "status": "Present" if work_time > 0 else "Absent"
        })

        
    return results

def calculate_detailed_machine_activity(db: Session, machine_id: str, target_date: date) -> List[dict]:
    """
    Get granular activity sessions for a specific machine on a given date.
    """
    logs = db.query(MachineRuntimeLog).filter(
        MachineRuntimeLog.machine_id == machine_id,
        MachineRuntimeLog.date == target_date
    ).order_by(MachineRuntimeLog.start_time.asc()).all()
    
    results = []
    now = get_current_time_ist()
    for log in logs:
        task = db.query(Task).filter(Task.id == log.task_id).first()
        
        # Determine operator for this interval
        user_log = db.query(UserWorkLog).filter(
            UserWorkLog.task_id == log.task_id,
            UserWorkLog.machine_id == machine_id,
            UserWorkLog.start_time <= log.start_time
        ).order_by(UserWorkLog.start_time.desc()).first()
        
        operator_name = "Unknown"
        if user_log:
            user = db.query(User).filter(User.user_id == user_log.user_id).first()
            operator_name = user.full_name or user.username if user else "Unknown"
        elif task:
            user = db.query(User).filter(User.user_id == task.assigned_to).first()
            operator_name = user.full_name or user.username if user else "Unknown"

        duration = log.duration_seconds or 0
        if log.end_time is None and log.date == get_today_date_ist():
            duration = int((now - log.start_time).total_seconds())

        results.append({
            "task_id": log.task_id,
            "task_title": task.title if task else "Deleted Task",
            "operator": operator_name,
            "start_time": log.start_time.isoformat(),
            "end_time": log.end_time.isoformat() if log.end_time else None,
            "runtime_seconds": max(0, duration),
            "expected_duration_minutes": task.expected_completion_time if task else 0,
            "held_time_seconds": task.total_held_seconds if task else 0,
            "status": "Running" if log.end_time is None else "Finished"
        })
    return results

def calculate_detailed_user_activity(db: Session, user_id: str, target_date: date) -> List[dict]:
    """
    Get granular activity sessions for a specific user on a given date with hold intervals.
    """
    logs = db.query(UserWorkLog).filter(
        UserWorkLog.user_id == user_id,
        UserWorkLog.date == target_date
    ).order_by(UserWorkLog.start_time.asc()).all()
    
    results = []
    now = get_current_time_ist()
    for log in logs:
        task = db.query(Task).filter(Task.id == log.task_id).first()
        machine = db.query(Machine).filter(Machine.id == log.machine_id).first() if log.machine_id else None
        
        holds = db.query(TaskHold).filter(TaskHold.task_id == log.task_id).all()
        hold_history = []
        for h in holds:
            h_end = h.hold_ended_at or (now if h.hold_started_at < now else h.hold_started_at)
            hold_history.append({
                "start": h.hold_started_at.isoformat(),
                "end": h.hold_ended_at.isoformat() if h.hold_ended_at else None,
                "reason": h.hold_reason,
                "duration_seconds": int((h_end - h.hold_started_at).total_seconds())
            })
        
        duration = log.duration_seconds or 0
        if log.end_time is None and log.date == get_today_date_ist():
            duration = int((now - log.start_time).total_seconds())

        results.append({
            "task_id": log.task_id,
            "task_title": task.title if task else "Deleted Task",
            "machine_name": machine.machine_name if machine else "Manual/Handwork",
            "start_time": log.start_time.isoformat(),
            "end_time": log.end_time.isoformat() if log.end_time else None,
            "duration_seconds": max(0, duration),
            "expected_duration_minutes": task.expected_completion_time if task else 0,
            "holds": hold_history,
            "status": "Running" if log.end_time is None else "Finished"
        })
    return results

def calculate_monthly_performance(db: Session, year: int) -> dict:
    # Aggregate by month for the year
    data_by_month = {m: {"total_tasks": 0, "total_duration": 0} for m in range(1, 13)}
    
    tasks = db.query(Task).filter(
        extract('year', Task.completed_at) == year,
        Task.status == 'completed',
        or_(Task.is_deleted == False, Task.is_deleted == None)
    ).all()
    
    for t in tasks:
        if t.completed_at:
            m = t.completed_at.month
            data_by_month[m]["total_tasks"] += 1
            
            d = t.total_duration_seconds or 0
            if d == 0 and t.actual_start_time and t.actual_end_time:
                elapsed = (t.actual_end_time - t.actual_start_time).total_seconds()
                held = t.total_held_seconds or 0
                d = max(0, int(elapsed - held))
            
            data_by_month[m]["total_duration"] += d
            
    chart_data = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    rows = [] # For CSV
    
    for m in range(1, 13):
        stats = data_by_month[m]
        count = stats["total_tasks"]
        duration = stats["total_duration"]
        
        aht_seconds = round(duration / count) if count > 0 else 0
        aht_mins = round((duration / count / 60), 2) if count > 0 else 0
        
        chart_data.append({
            "month": months[m-1],
            "tasks_completed": count,
            "aht": aht_mins
        })
        
        rows.append({
            "month": months[m-1],
            "tasks_completed": count,
            "total_runtime_hms": format_duration_hms(duration),
            "total_runtime_seconds": duration,
            "aht_hms": format_duration_hms(aht_seconds),
            "aht_seconds": aht_seconds
        })
        
    return {"year": year, "chart_data": chart_data, "csv_rows": rows}

# ----------------------------------------------------------------------
# ENDPOINTS
# ----------------------------------------------------------------------

@router.get("/machines/daily")
async def get_machine_daily_report(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """JSON Data for UI"""
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_machine_runtime(db, target_date)
    return {"date": target_date.isoformat(), "report": data}

@router.get("/users/daily")
async def get_user_daily_report(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """JSON Data for UI"""
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_user_activity(db, target_date)
    return {"date": target_date.isoformat(), "report": data}

@router.get("/monthly-performance")
async def get_monthly_performance(year: Optional[int] = None, db: Session = Depends(get_db)):
    """JSON Data for UI"""
    if not year:
        year = get_current_time_ist().year
    data = calculate_monthly_performance(db, year)
    return data # Returns chart_data inside

@router.get("/machines/export-csv")
async def export_machines_csv(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Standardized CSV: machine_summary_daily_YYYY-MM-DD.csv
    Columns: Machine ID, Machine Name, Unit, Category, Date, Total Running Time (HH:MM:SS), Total Running Time (Seconds), Tasks Run Count
    """
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_machine_runtime(db, target_date)
    
    # Requirement: Date,Machine Name,Runtime (minutes),Tasks Completed,Status
    headers = ["Date", "Machine Name", "Runtime (minutes)", "Tasks Completed", "Status"]
    
    rows = []
    for row in data:
        rows.append([
            row['date'],
            row['machine_name'],
            int(row['runtime_seconds'] / 60), # Raw minutes
            row['tasks_run_count'],
            row['status']
        ])
    
    filename = f"machine_summary_daily_{target_date}.csv"
    stream = generate_csv_stream(headers, rows)
    
    response_headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=response_headers)

@router.get("/users/export-csv")
async def export_users_csv(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Standardized CSV: user_activity_daily_YYYY-MM-DD.csv
    Columns: User ID, Username, Role, Date, Total Work Time (HH:MM:SS), Total Work Time (Seconds), Tasks Worked Count, Machines Used
    """
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_user_activity(db, target_date)
    
    # Requirement: Date,User Name,Work Time (minutes),Tasks Completed,Status
    headers = ["Date", "User Name", "Work Time (minutes)", "Tasks Completed", "Status"]
    
    rows = []
    for row in data:
        rows.append([
            row['date'],
            row['full_name'] or row['username'],
            int(row['total_work_seconds'] / 60), # Raw minutes
            row['tasks_worked_count'],
            row['status']
        ])
        
    filename = f"user_activity_daily_{target_date}.csv"
    stream = generate_csv_stream(headers, rows)
    
    response_headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=response_headers)

@router.get("/monthly/export-csv")
async def export_monthly_performance_csv(year: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Standardized CSV: monthly_performance_YYYY.csv
    Columns: Month, Tasks Completed, Total Runtime (HH:MM:SS), Total Runtime (Seconds), Average Handling Time (HH:MM:SS), Average Handling Time (Seconds)
    """
    if not year:
        year = get_current_time_ist().year
        
    analysis = calculate_monthly_performance(db, year)
    csv_rows = analysis["csv_rows"]
    
    headers = [
        "Month", "Tasks Completed", "Total Runtime (HH:MM:SS)", "Total Runtime (Seconds)",
        "Average Handling Time (HH:MM:SS)", "Average Handling Time (Seconds)"
    ]
    
    rows = []
    for item in csv_rows:
        rows.append([
            item['month'],
            item['tasks_completed'],
            item['total_runtime_hms'],
            item['total_runtime_seconds'],
            item['aht_hms'],
            item['aht_seconds']
        ])
        
    filename = f"monthly_performance_{year}.csv"
    stream = generate_csv_stream(headers, rows)
    
    response_headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=response_headers)

@router.get("/projects/export-csv")
async def export_projects_summary_csv(year_month: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Standardized CSV: project_summary_YYYY-MM.csv
    Columns: Project ID, Project Name, Work Order Number, Client Name, Tasks Completed, Total Runtime (HH:MM:SS), Average Task Duration (HH:MM:SS)
    """
    # Parse YYYY-MM
    target_dt = get_today_date_ist()
    if year_month:
        try:
            target_dt = datetime.strptime(year_month, "%Y-%m").date()
        except ValueError:
            pass
            
    # Filter tasks completed in that month
    # We join Task -> Project
    tasks = db.query(Task).join(Project, Task.project_id == Project.project_id).filter(
        extract('year', Task.completed_at) == target_dt.year,
        extract('month', Task.completed_at) == target_dt.month,
        Task.status == 'completed',
        or_(Task.is_deleted == False, Task.is_deleted == None)
    ).all()
    
    # Aggregate by Project
    project_stats = {}
    
    for t in tasks:
        pid = t.project_obj.project_id
        if pid not in project_stats:
            project_stats[pid] = {
                "obj": t.project_obj,
                "count": 0,
                "duration": 0
            }
            
        d = t.total_duration_seconds or 0
        if d == 0 and t.actual_start_time and t.actual_end_time:
            elapsed = (t.actual_end_time - t.actual_start_time).total_seconds()
            held = t.total_held_seconds or 0
            d = max(0, int(elapsed - held))
            
        project_stats[pid]["count"] += 1
        project_stats[pid]["duration"] += d
        
    headers = [
        "Project ID", "Project Name", "Work Order Number", "Client Name",
        "Tasks Completed", "Total Runtime (HH:MM:SS)", "Average Task Duration (HH:MM:SS)"
    ]
    
    rows = []
    
    sorted_stats = sorted(project_stats.items(), key=lambda x: x[1]["obj"].project_name)
    
    for pid, stats in sorted_stats:
        count = stats["count"]
        duration = stats["duration"]
        avg_dur = round(duration / count) if count > 0 else 0
        
        rows.append([
            pid,
            stats["obj"].project_name,
            stats["obj"].work_order_number,
            stats["obj"].client_name,
            count,
            format_duration_hms(duration),
            format_duration_hms(avg_dur)
        ])
        
    filename = f"project_summary_{target_dt.year}-{target_dt.month:02d}.csv"
    stream = generate_csv_stream(headers, rows)
    
    response_headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=response_headers)
@router.get("/machine-detailed")
async def get_machine_detailed_report(
    machine_id: str,
    target_date: date = Query(default_factory=get_today_date_ist),
    db: Session = Depends(get_db)
):
    """
    Returns granular activity sessions for a machine on a specific date.
    """
    return calculate_detailed_machine_activity(db, machine_id, target_date)

@router.get("/user-detailed")
async def get_user_detailed_report(
    user_id: str,
    target_date: date = Query(default_factory=get_today_date_ist),
    db: Session = Depends(get_db)
):
    """
    Returns granular activity sessions for a user on a specific date.
    """
    return calculate_detailed_user_activity(db, user_id, target_date)

@router.get("/active-monitoring")
async def get_active_work_monitoring(db: Session = Depends(get_db)):
    """
    Live view of all currently running tasks across the shop floor.
    """
    from app.routers.supervisor_router import get_running_tasks
    # Reuse the powerful supervisor logic
    res = await get_running_tasks(db)
    return res
