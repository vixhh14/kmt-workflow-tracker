from fastapi import APIRouter, HTTPException, Depends, Query
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
)

# ----------------------------------------------------------------------
# HELPER FUNCTIONS (Aggregation Logic)
# ----------------------------------------------------------------------

def calculate_detailed_machine_activity(db: any, machine_id: str, target_date: date) -> List[dict]:
    p = target_date.isoformat()
    from app.models.models_db import FilingTask, FabricationTask
    
    logs = [l for l in db.query(MachineRuntimeLog).all() if str(l.machine_id) == str(machine_id) and str(l.date).startswith(p)]
    
    # Pre-build unified task map
    gen = {str(t.id): t for t in db.query(Task).all()}
    filing = {str(t.id): t for t in db.query(FilingTask).all()}
    fab = {str(t.id): t for t in db.query(FabricationTask).all()}
    tasks = {**gen, **filing, **fab}
    
    users = {str(u.user_id): u for u in db.query(User).all()}
    
    res = []
    for l in logs:
        t = tasks.get(str(l.task_id))
        title = "Unknown"
        if t:
            title = getattr(t, 'title', getattr(t, 'part_item', 'Untitled'))
            
        res.append({
            "task_id": str(l.task_id),
            "task_title": title,
            "operator": users.get(str(t.assigned_to)).username if t and str(getattr(t, 'assigned_to', '')) in users else "Unknown",
            "start_time": str(l.start_time),
            "end_time": str(l.end_time or ""),
            "runtime_seconds": int(l.duration_seconds or 0),
            "status": "Completed" if l.end_time else "In Progress"
        })
    return res

def calculate_detailed_user_activity(db: any, user_id: str, target_date: date) -> List[dict]:
    p = target_date.isoformat()
    from app.models.models_db import FilingTask, FabricationTask

    logs = [l for l in db.query(UserWorkLog).all() if str(l.user_id) == str(user_id) and str(l.date).startswith(p)]
    
    # Pre-build unified task map
    gen = {str(t.id): t for t in db.query(Task).all()}
    filing = {str(t.id): t for t in db.query(FilingTask).all()}
    fab = {str(t.id): t for t in db.query(FabricationTask).all()}
    tasks = {**gen, **filing, **fab}
    
    machines = {str(m.id): m for m in db.query(Machine).all()}
    
    res = []
    for l in logs:
        t = tasks.get(str(l.task_id))
        m = machines.get(str(l.machine_id))
        title = "Unknown"
        if t:
            title = getattr(t, 'title', getattr(t, 'part_item', 'Untitled'))
            
        res.append({
            "task_id": str(l.task_id),
            "task_title": title,
            "machine_name": m.machine_name if m else "None",
            "start_time": str(l.start_time),
            "end_time": str(l.end_time or ""),
            "duration_seconds": int(l.duration_seconds or 0),
            "status": "Completed" if l.end_time else "In Progress"
        })
    return res

# Helper functions refactored for SheetsDB
def calculate_machine_runtime(db: any, target_date: date) -> List[dict]:
    target_date_str = target_date.isoformat()
    from app.models.models_db import FilingTask, FabricationTask
    
    # 1. Fetch Machines
    all_machines = db.query(Machine).all()
    machines = [m for m in all_machines if not getattr(m, 'is_deleted', False)]
    
    units = {str(getattr(u, 'unit_id', getattr(u, 'id', ''))): str(u.name) for u in db.query(Unit).all()}
    categories = {str(c.id): str(c.name) for c in db.query(MachineCategory).all()}
    
    # 2. Daily Logs for Runtime
    logs = [l for l in db.query(MachineRuntimeLog).all() if str(l.date).startswith(target_date_str)]
    
    # 3. Tasks completed across all 3 sheets
    def get_comp_date(t): return str(getattr(t, 'completed_at', '') or getattr(t, 'actual_end_time', '') or '')

    completed_gen = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False) and str(t.status).lower() == 'completed' and get_comp_date(t).startswith(target_date_str)]
    completed_filing = [t for t in db.query(FilingTask).all() if not getattr(t, 'is_deleted', False) and str(t.status).lower() == 'completed' and get_comp_date(t).startswith(target_date_str)]
    completed_fab = [t for t in db.query(FabricationTask).all() if not getattr(t, 'is_deleted', False) and str(t.status).lower() == 'completed' and get_comp_date(t).startswith(target_date_str)]
    
    all_completed = completed_gen + completed_filing + completed_fab

    # 4. Aggregate Stats
    machine_stats = {}
    for m in machines:
        mid = str(getattr(m, 'machine_id', getattr(m, 'id', '')))
        machine_stats[mid] = {"runtime": 0, "completed_tasks": 0, "is_running_now": False, "obj": m}
    
    for log in logs:
        mid_str = str(log.machine_id)
        if mid_str in machine_stats:
            machine_stats[mid_str]["runtime"] += int(log.duration_seconds or 0)
            if not log.end_time: # Still running
                machine_stats[mid_str]["is_running_now"] = True
    
    for t in all_completed:
        mid_str = str(t.machine_id)
        if mid_str in machine_stats:
            machine_stats[mid_str]["completed_tasks"] += 1
            
    results = []
    for m_id, stats in machine_stats.items():
        m = stats["obj"]
        m_id_actual = str(getattr(m, 'machine_id', getattr(m, 'id', '')))
        
        # More descriptive status for machines
        status_label = "Idle"
        if stats["is_running_now"]:
            status_label = "In Use"
        elif stats["runtime"] > 0:
            status_label = "Active"
            
        results.append({
            "machine_id": m_id_actual,
            "machine_name": str(m.machine_name),
            "unit": units.get(str(getattr(m, 'unit_id', getattr(m, 'id', ''))), ""),
            "category": categories.get(str(getattr(m, 'category_id', getattr(m, 'id', ''))), ""),
            "date": target_date_str,
            "runtime_seconds": stats["runtime"],
            "tasks_run_count": stats["completed_tasks"],
            "is_running_now": stats["is_running_now"],
            "status": status_label
        })
    return results

def calculate_user_activity(db: any, target_date: date) -> List[dict]:
    target_date_str = target_date.isoformat()
    from app.models.models_db import FilingTask, FabricationTask
    
    # 1. Fetch Users (Operators & Masters)
    users = []
    all_users = db.query(User).all()
    for u in all_users:
        if getattr(u, 'is_deleted', False): continue
        if str(getattr(u, 'role', '')).lower() not in ['operator', 'supervisor', 'fab_master', 'file_master']:
            continue
        approval = str(getattr(u, 'approval_status', 'approved')).lower().strip()
        if approval in ['pending', 'rejected']:
            continue
        users.append(u)
    
    # 2. Daily Logs for Work Time
    logs = [l for l in db.query(UserWorkLog).all() if str(l.date).startswith(target_date_str)]
    
    # 3. Tasks completed across all 3 sheets
    def get_comp_date(t): return str(getattr(t, 'completed_at', '') or getattr(t, 'actual_end_time', '') or '')

    completed_gen = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False) and str(t.status).lower() == 'completed' and get_comp_date(t).startswith(target_date_str)]
    completed_filing = [t for t in db.query(FilingTask).all() if not getattr(t, 'is_deleted', False) and str(t.status).lower() == 'completed' and get_comp_date(t).startswith(target_date_str)]
    completed_fab = [t for t in db.query(FabricationTask).all() if not getattr(t, 'is_deleted', False) and str(t.status).lower() == 'completed' and get_comp_date(t).startswith(target_date_str)]
    
    all_completed = completed_gen + completed_filing + completed_fab

    # 4. Attendance sync - Robust matching
    attendance_data = db.query(Attendance).all()
    attendees = set()
    for att in attendance_data:
        # Normalize date for comparison
        raw_att_date = str(getattr(att, 'date', getattr(att, 'check_in', '')))
        if not raw_att_date: continue
        
        att_day = raw_att_date.split('T')[0].split(' ')[0]
        # Handle DD/MM/YYYY vs YYYY-MM-DD
        if '/' in att_day:
            p = att_day.split('/')
            if len(p) == 3:
                # If it looks like DD/MM/YYYY
                if len(p[0]) <= 2: att_day = f"{p[2]}-{int(p[1]):02d}-{int(p[0]):02d}"
        
        if att_day == target_date_str:
            attendees.add(str(getattr(att, 'user_id', '')).strip().lower())

    # 5. Aggregate Stats
    user_stats = {str(u.user_id): {"work_time": 0, "completed_tasks": 0, "obj": u, "machines": set()} for u in users}
    
    for log in logs:
        uid_str = str(log.user_id)
        if uid_str in user_stats:
            user_stats[uid_str]["work_time"] += int(log.duration_seconds or 0)
            if log.machine_id: 
                user_stats[uid_str]["machines"].add(str(log.machine_id))
            
    for t in all_completed:
        uid_str = str(t.assigned_to)
        if uid_str in user_stats:
            user_stats[uid_str]["completed_tasks"] += 1
            
    return [{
        "user_id": uid,
        "username": str(s["obj"].username),
        "full_name": str(s["obj"].full_name or s["obj"].username),
        "date": target_date_str,
        "tasks_worked_count": s["completed_tasks"],
        "total_work_seconds": s["work_time"],
        "machines_used": list(s["machines"]),
        "status": "Present" if (s["work_time"] > 0 or str(uid).strip().lower() in attendees or s["completed_tasks"] > 0) else "Absent"
    } for uid, s in user_stats.items()]

def calculate_monthly_performance(db: any, year: int) -> dict:
    completed_in_year = [t for t in db.query(Task).all() if not t.is_deleted and str(t.status).lower() == 'completed' and t.completed_at and str(t.completed_at).startswith(str(year))]
    
    data_by_month = {m: {"total_tasks": 0, "total_duration": 0} for m in range(1, 13)}
    
    for t in completed_in_year:
        try:
            month = int(str(t.completed_at).split('-')[1])
            data_by_month[month]["total_tasks"] += 1
            data_by_month[month]["total_duration"] += int(t.total_duration_seconds or 0)
        except: pass
        
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    chart_data = []
    csv_rows = []
    
    for m in range(1, 13):
        stats = data_by_month[m]
        count = stats["total_tasks"]
        dur = stats["total_duration"]
        aht_mins = round(dur / count / 60, 2) if count > 0 else 0
        aht_sec = round(dur / count) if count > 0 else 0
        
        chart_data.append({"month": months[m-1], "tasks_completed": count, "aht": aht_mins})
        csv_rows.append({
            "month": months[m-1], "tasks_completed": count, 
            "total_runtime_hms": format_duration_hms(dur), "total_runtime_seconds": dur,
            "aht_hms": format_duration_hms(aht_sec), "aht_seconds": aht_sec
        })
        
    return {"year": year, "chart_data": chart_data, "csv_rows": csv_rows}

# Endpoints
@router.get("/machines/daily")
async def get_machine_daily_report(date_str: Optional[str] = None, db: any = Depends(get_db)):
    target_date = get_today_date_ist()
    if date_str:
        try: target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except: pass
    return {"date": target_date.isoformat(), "report": calculate_machine_runtime(db, target_date)}

@router.get("/users/daily")
async def get_user_daily_report(date_str: Optional[str] = None, db: any = Depends(get_db)):
    target_date = get_today_date_ist()
    if date_str:
        try: target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except: pass
    return {"date": target_date.isoformat(), "report": calculate_user_activity(db, target_date)}

@router.get("/monthly-performance")
async def get_monthly_performance(year: Optional[int] = None, db: any = Depends(get_db)):
    if not year: year = get_current_time_ist().year
    return calculate_monthly_performance(db, year)

@router.get("/machines/export-csv")
async def export_machines_csv(date_str: Optional[str] = None, db: any = Depends(get_db)):
    target_date = get_today_date_ist()
    if date_str:
        try: target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except: pass
    data = calculate_machine_runtime(db, target_date)
    headers = ["Date", "Machine Name", "Runtime (Mins)", "Tasks Run", "Status"]
    rows = [[d["date"], d["machine_name"], round(d["runtime_seconds"]/60, 2), d["tasks_run_count"], d["status"]] for d in data]
    stream = generate_csv_stream(headers, rows)
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={'Content-Disposition': f'attachment; filename="machine_report_{target_date}.csv"'})

@router.get("/users/export-csv")
async def export_users_csv(date_str: Optional[str] = None, db: any = Depends(get_db)):
    target_date = get_today_date_ist()
    if date_str:
        try: target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except: pass
    data = calculate_user_activity(db, target_date)
    headers = ["Date", "User Name", "Work Time (Mins)", "Tasks Worked", "Status"]
    rows = [[d["date"], d["full_name"], round(d["total_work_seconds"]/60, 2), d["tasks_worked_count"], d["status"]] for d in data]
    stream = generate_csv_stream(headers, rows)
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={'Content-Disposition': f'attachment; filename="user_report_{target_date}.csv"'})

@router.get("/monthly/export-csv")
async def export_monthly_performance_csv(year: Optional[int] = None, db: any = Depends(get_db)):
    if not year: year = get_current_time_ist().year
    analysis = calculate_monthly_performance(db, year)
    headers = ["Month", "Tasks Completed", "Total Runtime (HMS)", "Average Time (HMS)"]
    rows = [[r["month"], r["tasks_completed"], r["total_runtime_hms"], r["aht_hms"]] for r in analysis["csv_rows"]]
    stream = generate_csv_stream(headers, rows)
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={'Content-Disposition': f'attachment; filename="monthly_performance_{year}.csv"'})

@router.get("/projects/export-csv")
async def export_projects_summary_csv(year_month: Optional[str] = None, db: any = Depends(get_db)):
    target_dt = get_today_date_ist()
    if year_month:
        try: target_dt = datetime.strptime(year_month, "%Y-%m").date()
        except: pass
    pattern = f"{target_dt.year}-{target_dt.month:02d}"
    
    all_tasks = db.query(Task).all()
    tasks = [t for t in all_tasks if not t.is_deleted and str(t.status).lower() == 'completed' and str(t.completed_at).startswith(pattern)]
    
    p_all = {str(p.id or p.project_id): p for p in db.query(Project).all()}
    stats = {}
    for t in tasks:
        pid = str(t.project_id)
        if pid not in stats: stats[pid] = {"count": 0, "dur": 0, "obj": p_all.get(pid)}
        stats[pid]["count"] += 1
        stats[pid]["dur"] += int(t.total_duration_seconds or 0)
        
    headers = ["Project Name", "Work Order", "Client", "Tasks", "Total Runtime"]
    rows = []
    for pid, s in stats.items():
        if not s["obj"]: continue
        rows.append([str(s["obj"].project_name), str(s["obj"].work_order_number), str(s["obj"].client_name), s["count"], format_duration_hms(s["dur"])])
        
    stream = generate_csv_stream(headers, rows)
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={'Content-Disposition': f'attachment; filename="project_summary_{pattern}.csv"'})

@router.get("/machine-detailed")
async def get_machine_detailed_report(
    machine_id: str,
    target_date: date = Query(default_factory=get_today_date_ist),
    db: any = Depends(get_db)
):
    """
    Returns granular activity sessions for a machine on a specific date.
    """
    data = calculate_detailed_machine_activity(db, machine_id, target_date)
    for item in data:
        item["task_id"] = str(item["task_id"])
    return data

@router.get("/user-detailed")
async def get_user_detailed_report(
    user_id: str,
    target_date: date = Query(default_factory=get_today_date_ist),
    db: any = Depends(get_db)
):
    """
    Returns granular activity sessions for a user on a specific date.
    """
    data = calculate_detailed_user_activity(db, user_id, target_date)
    for item in data:
        item["task_id"] = str(item["task_id"])
    return data

@router.get("/active-monitoring")
async def get_active_work_monitoring(db: any = Depends(get_db)):
    """
    Live view of all currently running tasks across the shop floor.
    """
    from app.routers.supervisor_router import get_running_tasks
    # Reuse the powerful supervisor logic
    res = await get_running_tasks("all", "all", db)
    return res

@router.get("/machines/detailed-csv")
async def export_machine_detailed_csv(machine_id: str, date_str: Optional[str] = None, db: any = Depends(get_db)):
    """Detailed activity list for a machine."""
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_detailed_machine_activity(db, machine_id, target_date)
    
    headers = ["Task Title", "Operator", "Start Time", "End Time", "Runtime (Secs)", "Status"]
    rows = []
    for d in data:
        rows.append([
            d["task_title"],
            d["operator"],
            d["start_time"],
            d["end_time"],
            d["runtime_seconds"],
            d["status"]
        ])
        
    filename = f"machine_detailed_{machine_id}_{target_date}.csv"
    stream = generate_csv_stream(headers, rows)
    response_headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=response_headers)

@router.get("/users/detailed-csv")
async def export_user_detailed_csv(user_id: str, date_str: Optional[str] = None, db: any = Depends(get_db)):
    """Detailed activity list for a user."""
    target_date = get_today_date_ist()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    data = calculate_detailed_user_activity(db, user_id, target_date)
    
    headers = ["Task Title", "Machine", "Start Time", "End Time", "Duration (Secs)", "Status"]
    rows = []
    for d in data:
        rows.append([
            d["task_title"],
            d["machine_name"],
            d["start_time"],
            d["end_time"],
            d["duration_seconds"],
            d["status"]
        ])
        
    filename = f"user_detailed_{user_id}_{target_date}.csv"
    stream = generate_csv_stream(headers, rows)
    response_headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=response_headers)
