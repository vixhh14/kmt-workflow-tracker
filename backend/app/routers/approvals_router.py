"""
User Approvals Router - API endpoints for user approval workflow
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db
from ..models.models_db import User as UserModel

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

class ApprovalAction(BaseModel):
    notes: Optional[str] = None

@router.get("/pending")
async def get_pending_approvals(db: any = Depends(get_db)):
    """Get all pending user approvals using Google Sheets Backend."""
    all_users = db.query(UserModel).all()
    pending_users = [u for u in all_users if str(getattr(u, 'approval_status', '')).lower() == 'pending' and not getattr(u, 'is_deleted', False)]
    
    approvals = []
    for u in pending_users:
        u_id = str(getattr(u, 'id', ''))
        approvals.append({
            "id": u_id,
            "status": 'pending',
            "created_at": str(getattr(u, 'created_at', '')),
            "user": {
                "username": str(getattr(u, 'username', '')),
                "full_name": str(getattr(u, 'full_name', '') or getattr(u, 'username', '')),
                "email": str(getattr(u, 'email', '') or ""),
                "contact_number": str(getattr(u, 'contact_number', '') or ""),
                "unit_id": str(getattr(u, 'unit_id', '') or "")
            }
        })
    return approvals

@router.post("/{user_id}/approve")
async def approve_user(user_id: str, action: ApprovalAction, approved_by: str = "admin", db: any = Depends(get_db)):
    user = db.query(UserModel).filter(id=user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.approval_status = 'approved'
    user.updated_at = get_current_time_ist().isoformat()
    if action.notes: user.notes = action.notes
    db.commit()
    return {"message": f"User {user_id} approved"}

@router.post("/{user_id}/reject")
async def reject_user(user_id: str, action: ApprovalAction, rejected_by: str = "admin", db: any = Depends(get_db)):
    user = db.query(UserModel).filter(id=user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.approval_status = 'rejected'
    user.updated_at = get_current_time_ist().isoformat()
    if action.notes: user.notes = action.notes
    db.commit()
    return {"message": f"User {user_id} rejected"}
