"""
User Approvals Router - API endpoints for user approval workflow
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db
from ..models.models_db import User as UserModel
from ..core.time_utils import get_current_time_ist

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
    
    from app.repositories.sheets_repository import sheets_repo
    from app.core.time_utils import get_current_time_ist
    
    update_data = {
        "approval_status": 'approved',
        "updated_at": get_current_time_ist().isoformat()
    }
    if action.notes: update_data["notes"] = action.notes
    
    success = sheets_repo.update("users", user_id, update_data)
    if not success: raise HTTPException(status_code=500, detail="Failed to update Google Sheets")
    
    return {"message": f"User {user_id} approved"}

@router.post("/{user_id}/reject")
async def reject_user(user_id: str, action: ApprovalAction, rejected_by: str = "admin", db: any = Depends(get_db)):
    user = db.query(UserModel).filter(id=user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    from app.repositories.sheets_repository import sheets_repo
    from app.core.time_utils import get_current_time_ist
    
    update_data = {
        "approval_status": 'rejected',
        "updated_at": get_current_time_ist().isoformat()
    }
    if action.notes: update_data["notes"] = action.notes
    
    success = sheets_repo.update("users", user_id, update_data)
    if not success: raise HTTPException(status_code=500, detail="Failed to update Google Sheets")
    
    return {"message": f"User {user_id} rejected"}
