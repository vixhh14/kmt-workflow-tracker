from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import attendance_service
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"],
    responses={404: {"description": "Not found"}},
)

class MarkPresentRequest(BaseModel):
    user_id: str

@router.post("/mark-present")
async def mark_present(
    request_data: MarkPresentRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Mark a user as present for today"""
    try:
        # Get client IP address
        ip_address = request.client.host if request.client else None
        
        result = attendance_service.mark_present(
            db=db,
            user_id=request_data.user_id,
            ip_address=ip_address
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to mark attendance"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark attendance: {str(e)}")


@router.post("/check-out")
async def check_out(
    request_data: MarkPresentRequest,
    db: Session = Depends(get_db)
):
    """Mark a user as checked out for today"""
    try:
        result = attendance_service.mark_checkout(
            db=db,
            user_id=request_data.user_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to mark check-out"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark check-out: {str(e)}")


@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    """Get attendance summary for today"""
    try:
        result = attendance_service.get_attendance_summary(db=db)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to get attendance summary"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get attendance summary: {str(e)}")
