from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, case
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.core.database import get_db
from app.core.time_utils import get_current_time_ist, get_today_date_ist, IST
from app.models.models_db import Task, TaskTimeLog, Machine, User, Attendance, MachineRuntimeLog, UserWorkLog
import csv
import io
from fastapi.responses import StreamingResponse

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
    Data source: machine_runtime_logs ONLY.
    """
    # Initialize all machines to 0
    machines = db.query(Machine).all()
    machine_stats = {m.id: {"runtime": 0, "tasks": set(), "is_running": False, "obj": m} for m in machines}
    
    # Fetch logs for the date
    logs = db.query(MachineRuntimeLog).filter(MachineRuntimeLog.date == target_date).all()
    
    now = get_current_time_ist()
    
    for log in logs:
        if log.machine_id not in machine_stats:
            continue
            
        # Calculate duration
        duration = log.duration_seconds
        
        # If log is currently open (running now)
        if log.end_time is None:
            # Simplification: If it started today, count duration so far
            current_run = (now - log.start_time).total_seconds()
            duration = int(current_run)
            machine_stats[log.machine_id]["is_running"] = True
            
        machine_stats[log.machine_id]["runtime"] += duration
        machine_stats[log.machine_id]["tasks"].add(log.task_id)

    results = []
    for m_id, stats in machine_stats.items():
        machine = stats["obj"]
        results.append({
            "machine_id": machine.id,
            "machine_name": machine.name,
            "date": target_date.isoformat(),
            "runtime_seconds": stats["runtime"],
            "tasks_completed": len(stats["tasks"]), # Actually "Tasks Worked On"
            "is_running_now": stats["is_running"],
            "status": machine.status
        })
        
    return results

def calculate_user_activity(db: Session, target_date: date) -> List[dict]:
    """
    Calculate user activity for a specific date (IST) using UserWorkLog.
    Data source: user_work_logs ONLY.
    """
    # Initialize operators logs
    users = db.query(User).filter(User.role == 'operator').all()
    user_stats = {
        u.user_id: {
            "duration": 0, 
            "tasks": set(), 
            "obj": u,
            "machines": set()
        } for u in users
    }
    
    # Fetch logs
    logs = db.query(UserWorkLog).filter(UserWorkLog.date == target_date).all()
    
    now = get_current_time_ist()
    
    for log in logs:
        if log.user_id not in user_stats:
            continue
            
        duration = log.duration_seconds
        
        if log.end_time is None:
            current_run = (now - log.start_time).total_seconds()
            duration = int(current_run)
            
        user_stats[log.user_id]["duration"] += duration
        user_stats[log.user_id]["tasks"].add(log.task_id)
        if log.machine_id:
            user_stats[log.user_id]["machines"].add(log.machine_id)
            
    results = []
    for u_id, stats in user_stats.items():
        user = stats["obj"]
        
        # Get attendance info separately (as auxiliary info)
        attendance = db.query(Attendance).filter(
            Attendance.user_id == u_id,
            Attendance.date == target_date
        ).first()

        # Get task titles
        task_titles = []
        if stats["tasks"]:
            titles = db.query(Task.title).filter(Task.id.in_(list(stats["tasks"]))).all()
            task_titles = [t[0] for t in titles]

        results.append({
            "user_id": user.user_id,
            "username": user.username,
            "full_name": user.full_name,
            "date": target_date.isoformat(),
            "attendance_status": attendance.status if attendance else "Absent",
            "check_in": attendance.check_in.isoformat() if attendance and attendance.check_in else None,
            "check_out": attendance.check_out.isoformat() if attendance and attendance.check_out else None,
            "tasks_completed": len(stats["tasks"]), # "Tasks Worked On"
            "total_work_seconds": stats["duration"],
            "task_titles": task_titles
        })
        
    return results

# ----------------------------------------------------------------------
# ENDPOINTS
# ----------------------------------------------------------------------

@router.get("/machines/daily")
async def get_machine_daily_report(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get daily machine runtime report.
    """
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_machine_runtime(db, target_date)
    return {
        "date": target_date.isoformat(),
        "report": data
    }

@router.get("/users/daily")
async def get_user_daily_report(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get daily user activity report.
    """
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_user_activity(db, target_date)
    return {
        "date": target_date.isoformat(),
        "report": data
    }

@router.get("/monthly-performance")
async def get_monthly_performance(year: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Get monthly performance metrics (AHT, Tasks Completed).
    Returns data for all months of the selected year.
    """
    if not year:
        year = get_current_time_ist().year
        
    # Aggregate by month
    # We query all completed tasks for the year
    
    data_by_month = {m: {"total_tasks": 0, "total_duration": 0} for m in range(1, 13)}
    
    tasks = db.query(Task).filter(
        extract('year', Task.completed_at) == year,
        Task.status == 'completed'
    ).all()
    
    for t in tasks:
        if t.completed_at:
            m = t.completed_at.month
            data_by_month[m]["total_tasks"] += 1
            data_by_month[m]["total_duration"] += (t.total_duration_seconds or 0)
            
    # Format for chart
    chart_data = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    for m in range(1, 13):
        stats = data_by_month[m]
        count = stats["total_tasks"]
        duration = stats["total_duration"]
        
        # AHT in minutes
        aht = round((duration / count / 60), 2) if count > 0 else 0
        
        chart_data.append({
            "month": months[m-1],
            "tasks_completed": count,
            "aht": aht
        })
        
    return {
        "year": year,
        "chart_data": chart_data
    }

@router.get("/machines/export-csv")
async def export_machines_csv(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Download daily machine report as CSV.
    """
    # Logic similar to Daily Report
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_machine_runtime(db, target_date)
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["Date", "Machine ID", "Machine Name", "Runtime (Seconds)", "Runtime (Formatted)", "Tasks Completed", "Running Now", "Status"])
    
    for row in data:
        # Format duration
        seconds = row['runtime_seconds']
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        formatted = f"{hours}h {minutes}m"
        
        writer.writerow([
            row['date'],
            row['machine_id'],
            row['machine_name'],
            row['runtime_seconds'],
            formatted,
            row['tasks_completed'],
            "Yes" if row['is_running_now'] else "No",
            row['status']
        ])
        
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="machine_report_{target_date}.csv"'
    }
    
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

@router.get("/users/export-csv")
async def export_users_csv(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Download daily user report as CSV.
    """
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_user_activity(db, target_date)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["Date", "User ID", "Name", "Attendance", "Check In", "Check Out", "Tasks Completed", "Total Work Time", "Task Titles"])
    
    for row in data:
        seconds = row['total_work_seconds']
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        formatted = f"{hours}h {minutes}m"
        
        writer.writerow([
            row['date'],
            row['user_id'],
            row['full_name'],
            row['attendance_status'],
            row['check_in'] or "N/A",
            row['check_out'] or "N/A",
            row['tasks_completed'],
            formatted,
            ", ".join(row['task_titles'])
        ])
        
    output.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="user_report_{target_date}.csv"'
    }
    
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)
