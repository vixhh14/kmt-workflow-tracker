from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.models_db import User, UserApproval
from app.core.dependencies import get_current_active_admin
from app.core.auth_utils import hash_password, verify_password

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_active_admin)]
)

class UserStatusUpdate(BaseModel):
    status: str  # approved, pending, rejected

class UserRoleUpdate(BaseModel):
    role: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)
    confirm_new_password: str

class ApproveUserRequest(BaseModel):
    unit_id: str
    machine_types: Optional[str] = "" 
    role: Optional[str] = "operator"


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: str
    approval_status: Optional[str]
    created_at: Optional[datetime] = None
    
    # Additional fields for approval view
    unit_id: Optional[str] = None
    machine_types: Optional[str] = None
    contact_number: Optional[str] = None

    class Config:
        orm_mode = True

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/pending-users", response_model=List[UserResponse])
async def get_pending_users(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.approval_status == "pending").all()
    return users

@router.put("/change-password")
async def change_admin_password(
    request: ChangePasswordRequest,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    # Verify old password
    if not verify_password(request.old_password, current_admin.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    # Check if new passwords match
    if request.new_password != request.confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
    
    # Update password
    current_admin.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/users/{username}/approve")
async def approve_user(
    username: str,
    request: ApproveUserRequest,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    from app.core.email_utils import send_approval_email
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.approval_status == "approved":
        raise HTTPException(status_code=400, detail="User is already approved")
        
    # Update user
    user.approval_status = "approved"
    user.unit_id = request.unit_id
    user.machine_types = request.machine_types
    
    # Update role if provided
    if request.role:
        user.role = request.role
    
    # Update or create approval record
    approval = db.query(UserApproval).filter(UserApproval.user_id == user.user_id).first()
    if approval:
        approval.status = "approved"
        approval.approved_by = current_admin.username
        approval.approved_at = datetime.utcnow()
    else:
        # Should exist from signup, but just in case
        new_approval = UserApproval(
            user_id=user.user_id,
            status="approved",
            approved_by=current_admin.username,
            approved_at=datetime.utcnow()
        )
        db.add(new_approval)
    
    db.commit()
    
    # Send email notification
    login_url = "https://kmt-workflow-tracker.vercel.app/login"
    
    if user.email:
        # We don't await this if it's sync, or we can make it async if needed.
        # The utils function is sync (smtplib).
        try:
            send_approval_email(user.email, user.username, login_url)
        except Exception as e:
            print(f"Failed to send email: {e}")
            # Don't fail the approval if email fails
    
    return {"message": f"User {username} approved and assigned to unit {request.unit_id}"}

@router.post("/users/{username}/reject")
async def reject_user(
    username: str,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.approval_status = "rejected"
    
    # Update approval record
    approval = db.query(UserApproval).filter(UserApproval.user_id == user.user_id).first()
    if approval:
        approval.status = "rejected"
        approval.approved_by = current_admin.username
        approval.approved_at = datetime.utcnow()
        
    db.commit()
    return {"message": f"User {username} rejected"}

@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, status_update: UserStatusUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.approval_status = status_update.status
    db.commit()
    db.refresh(user)
    return {"message": f"User status updated to {status_update.status}"}

@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role_update: UserRoleUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    return {"message": f"User role updated to {role_update.role}"}
