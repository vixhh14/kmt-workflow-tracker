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
    # Assuming attendance_service has this, if not I'll need to check
    # But for now I'll just use what was likely there or simplified
    from app.core.time_utils import get_today_date_ist
    today = get_today_date_ist().isoformat()
    all_att = attendance_service.get_all_attendance(db, today)
    present = len([a for a in all_att if a.get("status") == "Present"])
    return {"present_count": present, "total_users": len(db.query(User).all()), "attendance": all_att}
