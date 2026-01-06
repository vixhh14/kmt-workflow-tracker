# app/routers/users_router.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.schemas.user_schema import UserCreate, UserOut, UserUpdate
from app.core.database import get_db
from app.core.dependencies import get_current_active_admin
from app.models.models_db import User
from uuid import uuid4
import hashlib
from datetime import datetime
from app.core.time_utils import get_current_time_ist

router = APIRouter(prefix="/users", tags=["Users"])


from app.core.dependencies import get_current_active_admin, get_current_user

# --------------------------
# GET ALL USERS
# --------------------------
@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).filter(or_(User.is_deleted == False, User.is_deleted == None)).all()
    return [
        UserOut(
            user_id=u.user_id,
            username=u.username,
            full_name=u.full_name,
            role=u.role,
            email=u.email,
            updated_at=u.updated_at,
            id=u.user_id,
            name=u.username
        ) for u in users
    ]


# --------------------------
# CREATE USER
# --------------------------
@router.post("", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists (active)
    if db.query(User).filter(
        func.lower(User.username) == func.lower(user.username),
        or_(User.is_deleted == False, User.is_deleted == None)
    ).first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    # Check if email exists (active)
    if user.email and db.query(User).filter(
        func.lower(User.email) == func.lower(user.email),
        or_(User.is_deleted == False, User.is_deleted == None)
    ).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    from app.core.auth_utils import hash_password

    # Use bcrypt hashing consistent with auth system
    hashed_password = hash_password(user.password)
    
    new_user = User(
        user_id=str(uuid4()),
        username=user.username,
        email=user.email or "",
        password_hash=hashed_password,
        role=user.role,
        full_name=user.full_name or "",
        machine_types=user.machine_types or "",
        approval_status="approved", # Admin-created users are auto-approved
        is_deleted=False,
        updated_at=get_current_time_ist()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserOut(
        user_id=new_user.user_id,
        username=new_user.username,
        full_name=new_user.full_name,
        role=new_user.role,
        email=new_user.email,
        machine_types=new_user.machine_types,
        updated_at=new_user.updated_at
    )


# --------------------------
# UPDATE USER
# --------------------------
@router.put("/{user_id}")
def update_user_data(user_id: str, updates: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    update_data = updates.dict(exclude_none=True)
    
    # Uniqueness checks
    if "username" in update_data and update_data["username"] != user.username:
        if db.query(User).filter(
            func.lower(User.username) == func.lower(update_data["username"]),
            User.user_id != user_id,
            or_(User.is_deleted == False, User.is_deleted == None)
        ).first():
            raise HTTPException(status_code=400, detail="Username already taken")
            
    if "email" in update_data and update_data["email"] != user.email:
        if db.query(User).filter(
            func.lower(User.email) == func.lower(update_data["email"]),
            User.user_id != user_id,
            or_(User.is_deleted == False, User.is_deleted == None)
        ).first():
            raise HTTPException(status_code=400, detail="Email already taken")
    
    for key, value in update_data.items():
        setattr(user, key, value)
        
    user.updated_at = get_current_time_ist()
        
    db.commit()
    return {"message": "User updated successfully"}


# --------------------------
# DELETE USER
# --------------------------
@router.delete("/{user_id}")
def delete_user_data(
    user_id: str, 
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    # Requirement F: Prevent deleting currently logged-in admin
    if user_id == current_admin.user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Soft delete only
    user.is_deleted = True
    db.commit()
    return {"message": "User deleted successfully"}
