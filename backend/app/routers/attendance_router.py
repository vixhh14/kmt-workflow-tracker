from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, Any
from app.core.database import get_db
from app.services import attendance_service
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.models.models_db import User

router = APIRouter(prefix="/attendance", tags=["Attendance"])

class AttendanceMark(BaseModel):
    user_id: str

@router.post("/mark-present")
async def mark_present(data: AttendanceMark, request: Request, db: any = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    return attendance_service.mark_present(db, data.user_id, ip)

@router.post("/check-out")
async def check_out(data: AttendanceMark, db: any = Depends(get_db)):
    return attendance_service.mark_checkout(db, data.user_id)

@router.get("/summary")
async def get_summary(db: any = Depends(get_db)):
    from app.core.time_utils import get_today_date_ist
    today = get_today_date_ist().isoformat()
    return attendance_service.get_attendance_summary(db, today)
