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
        "user_id": u_id,
        "username": user_data.username,
        "role": user_data.role,
        "email": user_data.email,
        "active": True,
        "created_at": now,
        "password_hash": hash_password(user_data.password)
    }
    
    try:
        inserted = sheets_repo.insert("users", user_dict)
        return inserted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user to Google Sheets: {e}")

@router.get("/", response_model=List[UserOut])
async def list_users(exclude_id: Optional[str] = None, db: any = Depends(get_db)):
    """List all active users with safety guard."""
    all_u = db.query(User).all()
    
    # helper imports 
    from app.core.normalizer import safe_normalize_list, normalize_user_row, safe_bool, safe_str

    # 1. Convert to dicts
    u_dicts = [u.dict() if hasattr(u, 'dict') else u.__dict__ for u in all_u]

    # 2. Normalize
    normalized_users = safe_normalize_list(
        u_dicts,
        normalize_user_row,
        "user"
    )

    results = []
    for u in normalized_users:
        try:
            # 3. Skip if deleted (already handled by normalizer but safe to double check)
            if u['is_deleted']: continue
            
            # 4. Filter inactive
            if not u['active']: continue
                
            # 5. Filter Unapproved (if that logic is desired here)
            # RELAXED: Allow empty status as approved (legacy)
            status = u.get('approval_status', 'approved').lower().strip()
            if status in ['pending', 'rejected']:
                continue

            # 6. Skip excluded user
            if exclude_id and u['user_id'] == str(exclude_id):
                continue
            
            results.append(UserOut(**u))
        except Exception as e:
            print(f"❌ [Users] Error processing user: {e}")
            
    return results

@router.get("/search", response_model=List[UserOut])
async def search_users(q: str, db: any = Depends(get_db)):
    """Search users with safety guard."""
    all_u = db.query(User).all()
    q = q.lower().strip()
    
    results = []
    for u in all_u:
        try:
            u_name = str(getattr(u, 'username', '')).lower()
            u_email = str(getattr(u, 'email', '') or "").lower()
            
            # Filter unapproved
            if str(getattr(u, 'approval_status', 'approved')).lower().strip() != 'approved':
                continue
            
            if q in u_name or q in u_email:
                results.append(UserOut(**u.dict()))
        except Exception as e:
            msg = getattr(u, 'username', 'Unknown')
            print(f"❌ [Users Search] Invalid row '{msg}' skipped: {e}")
            
    return results

@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(user_id: str, db: any = Depends(get_db)):
    u = db.query(User).filter(user_id=user_id).first()
    if not u or getattr(u, 'is_deleted', False): raise HTTPException(status_code=404, detail="User not found")
    return u

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, user_update: UserUpdate, db: any = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    u = db.query(User).filter(user_id=user_id).first()
    if not u or getattr(u, 'is_deleted', False): raise HTTPException(status_code=404, detail="User not found")
    
    from app.repositories.sheets_repository import sheets_repo
    from app.core.time_utils import get_current_time_ist
    
    # 1. Prepare Update Dictionary (Plain Dict)
    data = user_update.dict(exclude_unset=True)
    
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
    u = db.query(User).filter(user_id=user_id).first()
    if not u or getattr(u, 'is_deleted', False): raise HTTPException(status_code=404, detail="User not found")
    
    from app.repositories.sheets_repository import sheets_repo
    
    try:
        # 1. Soft Delete via Mandatory Status Update
        success = sheets_repo.update("users", user_id, {
            "active": False,
            "is_deleted": True
        })
        if not success: raise RuntimeError("Sheets update returned False")
        return {"message": "Deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user from Google Sheets: {e}")

@router.get("/{user_id}/operational-tasks")
async def get_user_operational_tasks(user_id: str, db: any = Depends(get_db)):
    """Fetch filing and fabrication tasks for a user."""
    from app.models.models_db import FilingTask, FabricationTask
    
    filing = [t.dict() for t in db.query(FilingTask).all() if str(getattr(t, 'assigned_to', '')).lower() == str(user_id).lower() and not getattr(t, 'is_deleted', False)]
    fabrication = [t.dict() for t in db.query(FabricationTask).all() if str(getattr(t, 'assigned_to', '')).lower() == str(user_id).lower() and not getattr(t, 'is_deleted', False)]
    
    return {
        "filing": filing,
        "fabrication": fabrication,
        "tasks": filing + fabrication
    }
