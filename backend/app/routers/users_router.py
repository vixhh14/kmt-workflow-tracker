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
    
    results = []
    for u in all_u:
        try:
            # 1. Skip if deleted or inactive
            is_del = str(getattr(u, 'is_deleted', 'False')).lower()
            if is_del in ['true', '1', 'yes']: continue
            
            is_active = str(getattr(u, 'active', 'true')).lower().strip()
            if is_active in ['false', '0', 'no', 'inactive']:
                continue
                
            # 2. Filter Unapproved Users (They belong in Pending Approvals only)
            # RELAXED CHECK: Allow empty/None as approved for legacy/migration safety
            status = str(getattr(u, 'approval_status', '')).lower().strip()
            if status not in ['approved', '', 'none', 'true']: 
                # If explicit 'pending' or 'rejected', skip. If empty, allow (legacy)
                if status in ['pending', 'rejected']:
                    continue

            # 3. Skip excluded user (usually self)
            u_id = str(getattr(u, 'user_id', getattr(u, 'id', '')))
            if exclude_id and u_id == str(exclude_id):
                continue
            
            # 3. Final Validation
            results.append(UserOut(**u.dict()))
        except Exception as e:
            msg = getattr(u, 'username', 'Unknown')
            print(f"❌ [Users] Invalid row '{msg}' skipped: {e}")
            
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
