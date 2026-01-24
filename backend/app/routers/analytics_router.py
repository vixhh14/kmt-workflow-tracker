from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Any
from datetime import datetime
from app.core.database import get_db
from app.models.models_db import Task, User
from app.services.dashboard_analytics_service import get_operations_overview

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview")
async def dashboard_overview(db: any = Depends(get_db)):
    """
    Unified dashboard overview for Admin, Supervisor, and Planning.
    """
    return get_operations_overview(db)

@router.get("/operator-performance")
async def get_operator_performance(
    month: int,
    year: int,
    operator_id: Optional[str] = None,
    db: any = Depends(get_db)
):
    all_tasks = db.query(Task).all()
    # Filter by month/year in memory from ISO string created_at (YYYY-MM-DD...)
    pattern = f"{year}-{month:02d}"
    tasks = [t for t in all_tasks if not t.is_deleted and str(t.created_at).startswith(pattern)]
    
    if operator_id:
        tasks = [t for t in tasks if str(t.assigned_to) == str(operator_id)]
        
    completed = [t for t in tasks if t.status == 'completed']
    total_dur = sum([int(t.total_duration_seconds or 0) for t in completed])
    
    pct = round((len(completed) / len(tasks) * 100), 2) if tasks else 0
    
    duration_by_date = {}
    for t in completed:
        if t.completed_at:
            d_str = str(t.completed_at).split('T')[0]
            duration_by_date[d_str] = duration_by_date.get(d_str, 0) + int(t.total_duration_seconds or 0)
            
    graph_data = [{"date": d, "duration": dur} for d, dur in sorted(duration_by_date.items())]
    
    return {
        "metrics": {
            "total_tasks": len(tasks),
            "completed_tasks": len(completed),
            "total_duration_minutes": round(total_dur / 60, 2),
            "efficiency": pct
        },
        "graph_data": graph_data
    }

@router.get("/task-distribution")
async def get_task_dist(db: any = Depends(get_db)):
    """Get task status distribution across ALL task types (general, filing, fabrication)"""
    from app.models.models_db import FilingTask, FabricationTask
    
    # Get all task types
    general_tasks = [t for t in db.query(Task).all() if not getattr(t, 'is_deleted', False)]
    filing_tasks = [t for t in db.query(FilingTask).all() if not getattr(t, 'is_deleted', False)]
    fab_tasks = [t for t in db.query(FabricationTask).all() if not getattr(t, 'is_deleted', False)]
    
    # Combine all tasks
    all_tasks = general_tasks + filing_tasks + fab_tasks
    
    print(f"📊 Task Distribution: {len(general_tasks)} general, {len(filing_tasks)} filing, {len(fab_tasks)} fabrication")
    
    # Count by status
    dist = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "on_hold": 0,
        "denied": 0
    }
    
    from app.core.normalizer import normalize_status
    
    for t in all_tasks:
        raw_status = getattr(t, 'status', 'pending')
        status = normalize_status(raw_status)
        
        # Ensure status key exists in dist
        dist[status] = dist.get(status, 0) + 1
    
    print(f"📊 Distribution: {dist}")
    return dist

@router.get("/production-trend")
async def get_prod_trend(year: Optional[int] = None, db: any = Depends(get_db)):
    if not year: year = datetime.now().year
    tasks = [t for t in db.query(Task).all() if not t.is_deleted and str(t.status).lower() == 'completed' and str(t.completed_at).startswith(str(year))]
    months = {m: 0 for m in range(1, 13)}
    for t in tasks:
        try:
            m = int(str(t.completed_at).split("-")[1])
            months[m] += 1
        except: pass
    ms = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return [{"month": ms[m-1], "completed": count} for m, count in months.items()]
