# app/routers/users_router.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.users_model import UserCreate, UserOut, UserUpdate
from app.core.database import get_db
from app.models.models_db import User
from uuid import uuid4
import hashlib
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])


# --------------------------
# GET ALL USERS
# --------------------------
@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        UserOut(
            user_id=u.user_id,
            username=u.username,
            full_name=u.full_name,
            role=u.role,
            email=u.email,
            updated_at=u.updated_at
        ) for u in users
    ]


# --------------------------
# CREATE USER
# --------------------------
@router.post("/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    
    new_user = User(
        user_id=str(uuid4()),
        username=user.username,
        email=user.email or "",
        password_hash=password_hash,
        role=user.role,
        full_name=user.full_name or "",
        machine_types=user.machine_types or "",
        updated_at=datetime.utcnow()
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
    
    for key, value in update_data.items():
        setattr(user, key, value)
        
    user.updated_at = datetime.utcnow()
        
    db.commit()
    return {"message": "User updated successfully"}


# --------------------------
# DELETE USER
# --------------------------
@router.delete("/{user_id}")
def delete_user_data(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}
