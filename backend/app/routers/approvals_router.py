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
    pending_users = [u for u in all_users if str(u.approval_status).lower() == 'pending' and not u.is_deleted]
    
    approvals = []
    for u in pending_users:
        approvals.append({
            "id": str(u.user_id),
            "user_id": str(u.user_id),
            "status": 'pending',
            "created_at": str(u.created_at),
            "user": {
                "username": str(u.username),
                "full_name": str(u.full_name or u.username),
                "email": str(u.email or ""),
                "contact_number": str(u.contact_number or ""),
                "unit_id": str(u.unit_id or "")
            }
        })
    return approvals

@router.post("/{user_id}/approve")
async def approve_user(user_id: str, action: ApprovalAction, approved_by: str = "admin", db: any = Depends(get_db)):
    user = db.query(UserModel).filter(user_id=user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.approval_status = 'approved'
    user.updated_at = datetime.now().isoformat()
    if action.notes: user.notes = action.notes
    db.commit()
    return {"message": f"User {user_id} approved"}

@router.post("/{user_id}/reject")
async def reject_user(user_id: str, action: ApprovalAction, rejected_by: str = "admin", db: any = Depends(get_db)):
    user = db.query(UserModel).filter(user_id=user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.approval_status = 'rejected'
    user.updated_at = datetime.now().isoformat()
    if action.notes: user.notes = action.notes
    db.commit()
    return {"message": f"User {user_id} rejected"}
