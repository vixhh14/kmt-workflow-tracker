"""
User Approvals Router - API endpoints for user approval workflow
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.models_db import UserApproval as UserApprovalModel, User as UserModel

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

class UserApproval(BaseModel):
    id: int
    user_id: str
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    user: Optional[dict] = None # To hold nested user data

    model_config = ConfigDict(from_attributes=True)

class ApprovalAction(BaseModel):
    notes: Optional[str] = None

@router.get("/pending")
async def get_pending_approvals(db: Session = Depends(get_db)):
    """Get all pending user approvals with user details"""
    results = db.query(UserApprovalModel, UserModel).join(
        UserModel, UserApprovalModel.user_id == UserModel.user_id
    ).filter(
        UserApprovalModel.status == 'pending',
        UserModel.is_deleted == False
    ).order_by(
        UserApprovalModel.created_at.desc()
    ).all()
    
    approvals = []
    for ua, u in results:
        approval_dict = {
            "id": ua.id,
            "user_id": ua.user_id,
            "status": ua.status,
            "approved_by": ua.approved_by,
            "approved_at": ua.approved_at,
            "notes": ua.notes,
            "created_at": ua.created_at,
            "user": {
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "date_of_birth": u.date_of_birth,
                "address": u.address,
                "contact_number": u.contact_number,
                "unit_id": u.unit_id
            }
        }
        approvals.append(approval_dict)
    
    return approvals

@router.post("/{user_id}/approve")
async def approve_user(user_id: str, action: ApprovalAction, approved_by: str = "admin", db: Session = Depends(get_db)):
    """Approve a user"""
    try:
        # Update approval record
        approval = db.query(UserApprovalModel).filter(UserApprovalModel.user_id == user_id).first()
        if approval:
            approval.status = 'approved'
            approval.approved_by = approved_by
            approval.approved_at = datetime.utcnow()
            approval.notes = action.notes
        
        # Update user status
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        if user:
            user.approval_status = 'approved'
        
        db.commit()
        return {"message": f"User {user_id} approved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{user_id}/reject")
async def reject_user(user_id: str, action: ApprovalAction, rejected_by: str = "admin", db: Session = Depends(get_db)):
    """Reject a user"""
    try:
        # Update approval record
        approval = db.query(UserApprovalModel).filter(UserApprovalModel.user_id == user_id).first()
        if approval:
            approval.status = 'rejected'
            approval.approved_by = rejected_by
            approval.approved_at = datetime.utcnow()
            approval.notes = action.notes
        
        # Update user status
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        if user:
            user.approval_status = 'rejected'
        
        db.commit()
        return {"message": f"User {user_id} rejected"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
