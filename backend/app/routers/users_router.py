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
    """Allow admin to create a new user manually using Sheets-native dict."""
    all_users = db.query(User).all()
    if any(str(getattr(u, 'username', '')).lower() == user_data.username.lower() for u in all_users):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    is_valid, errors = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors[0])
    
    from app.repositories.sheets_repository import sheets_repo
    from app.core.time_utils import get_current_time_ist
    
    u_id = str(uuid4())
    now = get_current_time_ist().isoformat()
    
    # 1. Build canonical dict
    user_dict = {
        **user_data.dict(exclude={'password'}),
        "user_id": u_id,
        "id": u_id,
        "password": hash_password(user_data.password), # Map to 'password' column
        "approval_status": 'approved',
        "is_active": True,
        "is_deleted": False,
        "created_at": now,
        "updated_at": now
    }
    
    try:
        inserted = sheets_repo.insert("users", user_dict)
        return inserted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user to Google Sheets: {e}")

@router.get("/", response_model=List[UserOut])
async def list_users(exclude_id: Optional[str] = None, db: any = Depends(get_db)):
    """List all active users from cache."""
    res = db.query(User).filter(is_deleted=False, active=True).all()
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
    
    from app.repositories.sheets_repository import sheets_repo
    from app.core.time_utils import get_current_time_ist
    
    # 1. Prepare Update Dictionary (Plain Dict)
    data = user_update.dict(exclude_unset=True)
    data["updated_at"] = get_current_time_ist().isoformat()
    
    try:
        # 2. Strict Sheet Write
        success = sheets_repo.update("users", user_id, data)
        if not success: raise RuntimeError("Sheets update returned False")
        
        # 3. Return combined state
        return {**u.dict(), **data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user in Google Sheets: {e}")

@router.delete("/{user_id}")
async def delete_user(user_id: str, db: any = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    u = db.query(User).filter(id=user_id).first()
    if not u or getattr(u, 'is_deleted', False): raise HTTPException(status_code=404, detail="User not found")
    
    from app.repositories.sheets_repository import sheets_repo
    from app.core.time_utils import get_current_time_ist
    
    try:
        # 1. Soft Delete via Mandatory Status Update
        success = sheets_repo.update("users", user_id, {
            "is_deleted": True,
            "is_active": False,
            "updated_at": get_current_time_ist().isoformat()
        })
        if not success: raise RuntimeError("Sheets update returned False")
        return {"message": "Deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user from Google Sheets: {e}")
