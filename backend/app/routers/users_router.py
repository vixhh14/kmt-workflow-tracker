from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from app.schemas.user_schema import UserCreate, UserOut, UserUpdate
from app.core.database import get_db
from app.core.dependencies import get_current_active_admin, get_current_user
from app.models.models_db import User
from uuid import uuid4

from app.core.auth_utils import hash_password
from app.core.password_validation import validate_password_strength

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserOut)
async def create_user(user_data: UserCreate, db: any = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    """Allow admin to create a new user manually."""
    all_users = db.query(User).all()
    if any(str(getattr(u, 'username', '')).lower() == user_data.username.lower() for u in all_users):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    is_valid, errors = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors[0])
    
    new_user = User(
        **user_data.dict(exclude={'password'}),
        password_hash=hash_password(user_data.password),
        approval_status='approved', # Admin added users are auto-approved
        active=True
    )
    db.add(new_user)
    db.commit()
    return new_user

@router.get("/", response_model=List[UserOut])
async def list_users(exclude_id: Optional[str] = None, db: any = Depends(get_db)):
    """List all active users from cache."""
    res = db.query(User).filter(is_deleted=False).all()
    if exclude_id:
        res = [u for u in res if str(getattr(u, 'id', '')) != str(exclude_id)]
    return res

@router.get("/search", response_model=List[UserOut])
async def search_users(q: str, db: any = Depends(get_db)):
    all_u = db.query(User).all()
    q = q.lower()
    return [u for u in all_u if not getattr(u, 'is_deleted', False) and (q in str(getattr(u, 'username', '')).lower() or q in str(getattr(u, 'email', '') or "").lower() or q in str(getattr(u, 'full_name', '') or "").lower())]

@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(user_id: str, db: any = Depends(get_db)):
    u = db.query(User).filter(id=user_id).first()
    if not u or getattr(u, 'is_deleted', False): raise HTTPException(status_code=404, detail="User not found")
    return u

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, user_update: UserUpdate, db: any = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    u = db.query(User).filter(id=user_id).first()
    if not u or getattr(u, 'is_deleted', False): raise HTTPException(status_code=404, detail="User not found")
    
    data = user_update.dict(exclude_none=True)
    for k, v in data.items():
        setattr(u, k, v)
    u.updated_at = datetime.now().isoformat()
    db.commit()
    return u

@router.delete("/{user_id}")
async def delete_user(user_id: str, db: any = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    u = db.query(User).filter(id=user_id).first()
    if not u or getattr(u, 'is_deleted', False): raise HTTPException(status_code=404, detail="User not found")
    u.is_deleted = True
    u.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Deleted"}
