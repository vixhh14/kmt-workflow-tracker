from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.core.database import get_db
from app.models.models_db import User
from app.core.dependencies import get_current_active_admin
from app.core.auth_utils import hash_password, verify_password

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_active_admin)]
)

class UserStatusUpdate(BaseModel):
    status: str
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
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    approval_status: Optional[str] = None
    created_at: Optional[str] = None
    unit_id: Optional[str] = None
    machine_types: Optional[str] = None
    contact_number: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

@router.get("/users", response_model=List[dict])
async def get_all_users(db: any = Depends(get_db)):
    return [u.dict() for u in db.query(User).all() if not u.is_deleted and str(u.approval_status).lower() == 'approved']

@router.get("/pending-users", response_model=List[dict])
async def get_pending_users(db: any = Depends(get_db)):
    return [u.dict() for u in db.query(User).all() if not u.is_deleted and str(u.approval_status).lower() == 'pending']

@router.get("/approvals")
async def get_admin_approvals(db: any = Depends(get_db)):
    pending = [u.dict() for u in db.query(User).all() if not u.is_deleted and str(u.approval_status).lower() == 'pending']
    return {"pending_users": pending}

@router.put("/change-password")
async def change_admin_password(request: ChangePasswordRequest, current_admin: User = Depends(get_current_active_admin), db: any = Depends(get_db)):
    if not verify_password(request.old_password, current_admin.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    if request.new_password != request.confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    user = db.query(User).filter(user_id=current_admin.user_id).first()
    user.password_hash = hash_password(request.new_password)
    user.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Success"}

@router.post("/users/{username}/approve")
async def approve_user(username: str, request: ApproveUserRequest, db: any = Depends(get_db)):
    user = db.query(User).filter(username=username).first()
    if not user: raise HTTPException(status_code=404, detail="Not found")
    user.approval_status = "approved"
    user.unit_id = request.unit_id
    user.machine_types = request.machine_types
    if request.role: user.role = request.role
    user.updated_at = datetime.now().isoformat()
    db.commit()
    try:
        from app.core.email_utils import send_approval_email
        if user.email: send_approval_email(user.email, user.username, "https://kmt-workflow-tracker.vercel.app/login")
    except: pass
    return {"message": "Approved"}

@router.post("/users/{username}/reject")
async def reject_user(username: str, db: any = Depends(get_db)):
    user = db.query(User).filter(username=username).first()
    if not user: raise HTTPException(status_code=404, detail="Not found")
    user.approval_status = "rejected"
    user.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Rejected"}

@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, status_update: UserStatusUpdate, db: any = Depends(get_db)):
    user = db.query(User).filter(user_id=user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Not found")
    user.approval_status = status_update.status
    user.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Updated"}

@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role_update: UserRoleUpdate, db: any = Depends(get_db)):
    user = db.query(User).filter(user_id=user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Not found")
    user.role = role_update.role
    user.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Updated"}
