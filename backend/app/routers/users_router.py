from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from app.schemas.user_schema import UserCreate, UserOut, UserUpdate
from app.core.database import get_db
from app.core.dependencies import get_current_active_admin, get_current_user
from app.models.models_db import User
from uuid import uuid4

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=List[UserOut])
async def list_users(exclude_id: Optional[str] = None, db: any = Depends(get_db)):
    users = db.query(User).all()
    res = [u for u in users if not u.is_deleted]
    if exclude_id:
        res = [u for u in res if str(u.user_id) != str(exclude_id)]
    return res

@router.get("/search", response_model=List[UserOut])
async def search_users(q: str, db: any = Depends(get_db)):
    all_u = db.query(User).all()
    q = q.lower()
    return [u for u in all_u if not u.is_deleted and (q in str(u.username).lower() or q in str(u.email or "").lower() or q in str(u.full_name or "").lower())]

@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(user_id: str, db: any = Depends(get_db)):
    u = db.query(User).filter(user_id=user_id).first()
    if not u or u.is_deleted: raise HTTPException(status_code=404, detail="User not found")
    return u

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, user_update: UserUpdate, db: any = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    u = db.query(User).filter(user_id=user_id).first()
    if not u or u.is_deleted: raise HTTPException(status_code=404, detail="User not found")
    
    data = user_update.dict(exclude_none=True)
    for k, v in data.items():
        setattr(u, k, v)
    u.updated_at = datetime.now().isoformat()
    db.commit()
    return u

@router.delete("/{user_id}")
async def delete_user(user_id: str, db: any = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    u = db.query(User).filter(user_id=user_id).first()
    if not u or u.is_deleted: raise HTTPException(status_code=404, detail="User not found")
    u.is_deleted = True
    u.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Deleted"}
