from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import time
from app.models.auth_model import LoginRequest, LoginResponse, ChangePasswordRequest
from app.core.auth_utils import verify_password, create_access_token, hash_password
from app.core.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.models_db import User
from app.schemas.user_schema import UserUpdate
from app.core.password_validation import validate_password_strength

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, background_tasks: BackgroundTasks, db: any = Depends(get_db)):
    """
    Authenticate user and return JWT token using Google Sheets Backend.
    """
    from app.core.config import JWT_SECRET
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="Server security token missing")

    try:
        # Load all users from Sheets (cached)
        all_users = db.query(User).all()
        
        # Mandatory: Trim whitespace and check active
        u_name = credentials.username.strip().lower()
        user = next((u for u in all_users if str(getattr(u, 'username', '')).strip().lower() == u_name and getattr(u, 'active', False) and not getattr(u, 'is_deleted', False)), None)

        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        # Standardize on role everywhere as per core principles
        role = str(getattr(user, 'role', 'operator') or "operator").lower().strip()

        # Status check
        if not bool(getattr(user, 'active', True)):
            raise HTTPException(status_code=403, detail="Account is inactive")
        
        # Password verification
        u_hash = getattr(user, 'password_hash', None)
        if not u_hash:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        if not verify_password(credentials.password, u_hash):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        # JWT Token
        u_id = str(getattr(user, 'user_id', getattr(user, 'id', '')))
        token_data = {"sub": str(getattr(user, 'username', '')), "id": u_id, "role": role}
        access_token = create_access_token(data=token_data)
        
        # Mark Attendance (IST) in background
        def mark_attendance_bg(uid):
             try:
                 from app.services import attendance_service
                 from app.core.sheets_db import get_sheets_db
                 new_db = get_sheets_db()
                 attendance_service.mark_present(db=new_db, user_id=uid)
             except Exception as e:
                 print(f"Background Attendance mark failed: {e}")

        background_tasks.add_task(mark_attendance_bg, u_id)
 
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": u_id,
                "user_id": u_id,
                "username": str(getattr(user, 'username', '')),
                "email": str(getattr(user, 'email', '') or ""),
                "role": role
            }
        )
    except HTTPException: raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/me")
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    """Get current logged in user profile"""
    return {
        "id": getattr(current_user, 'id', ''),
        "username": getattr(current_user, 'username', ''),
        "email": getattr(current_user, 'email', ''),
        "role": getattr(current_user, 'role', ''),
        "full_name": getattr(current_user, 'full_name', ''),
        "unit_id": getattr(current_user, 'unit_id', ''),
        "machine_types": getattr(current_user, 'machine_types', ''),
        "created_at": getattr(current_user, 'created_at', ''),
        "contact_number": getattr(current_user, 'contact_number', ''),
        "security_question": getattr(current_user, 'security_question', '')
    }

@router.put("/profile")
async def update_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: any = Depends(get_db)
):
    """Update current user's profile information"""
    update_data = updates.dict(exclude_none=True)
    all_users = db.query(User).all()
    
    current_uid = getattr(current_user, 'id', '')
    
    # Check uniqueness
    if "username" in update_data and update_data["username"] != getattr(current_user, 'username', ''):
        if any(getattr(u, 'username', '') == update_data["username"] and getattr(u, 'id', '') != current_uid for u in all_users):
            raise HTTPException(status_code=400, detail="Username taken")
            
    if "email" in update_data and update_data["email"] != getattr(current_user, 'email', ''):
        if any(getattr(u, 'email', '') == update_data["email"] and getattr(u, 'id', '') != current_uid for u in all_users):
            raise HTTPException(status_code=400, detail="Email taken")

    # Update row
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    current_user.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return {"message": "Profile updated successfully"}

class ForgotPasswordRequest(BaseModel):
    username: str

@router.post("/get-security-question")
async def get_security_question(request: ForgotPasswordRequest, db: any = Depends(get_db)):
    """Get security question for a user (forgot password step 1)"""
    all_users = db.query(User).all()
    user = next((u for u in all_users if (str(getattr(u, 'username', '')).lower() == request.username.lower() or str(getattr(u, 'email', '') or "").lower() == request.username.lower()) and not getattr(u, 'is_deleted', False)), None)
    
    s_q = getattr(user, 'security_question', None)
    if not user or not s_q:
        raise HTTPException(status_code=404, detail="Security question not set or user not found")
        
    return {"question": s_q}

class ResetPasswordRequest(BaseModel):
    username: str
    security_answer: str
    new_password: str

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: any = Depends(get_db)):
    """Reset password using security answer (forgot password step 2)"""
    all_users = db.query(User).all()
    user = next((u for u in all_users if (str(getattr(u, 'username', '')).lower() == request.username.lower() or str(getattr(u, 'email', '') or "").lower() == request.username.lower()) and not getattr(u, 'is_deleted', False)), None)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if str(getattr(user, 'security_answer', '')).lower() != request.security_answer.lower():
        raise HTTPException(status_code=400, detail="Incorrect security answer")
        
    is_valid, errors = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors[0])
        
    user.password_hash = hash_password(request.new_password)
    user.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return {"message": "Password reset successfully"}

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: any = Depends(get_db)
):
    """Change password for logged in user"""
    if not verify_password(request.current_password, getattr(current_user, 'password_hash', '')):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    if request.new_password != request.confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    is_valid, errors = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors[0])
        
    current_user.password_hash = hash_password(request.new_password)
    current_user.updated_at = get_current_time_ist().isoformat()
    db.commit()
    return {"message": "Password changed successfully"}

@router.post("/signup")
async def signup(user_data: dict, db: any = Depends(get_db)):
    """
    Register new user.
    User will be in 'pending' status until admin approves.
    """
    from app.repositories.sheets_repository import sheets_repo
    from app.core.time_utils import get_current_time_ist
    import uuid

    # 1. Basic Validation
    required = ['username', 'password', 'email', 'full_name']
    for field in required:
        if not user_data.get(field):
            raise HTTPException(status_code=400, detail=f"{field} is required")

    # 2. Uniqueness Check (Cached)
    all_users = sheets_repo.get_all("users", include_deleted=True)
    if any(str(u.get('username', '')).lower() == str(user_data['username']).lower() for u in all_users):
        raise HTTPException(status_code=400, detail="Username exists")
    
    if any(str(u.get('email', '')).lower() == str(user_data['email']).lower() for u in all_users):
        raise HTTPException(status_code=400, detail="Email exists")
    
    is_valid, errors = validate_password_strength(user_data['password'])
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors[0])
    
    # 3. Create canonical dictionary
    u_id = str(uuid.uuid4())
    now = get_current_time_ist().isoformat()
    
    new_user_dict = {
        "user_id": u_id,
        "username": user_data['username'],
        "role": 'operator',
        "email": user_data['email'],
        "active": True, # Always write active=TRUE as per mandatory rules
        "created_at": now,
        "password_hash": hash_password(user_data['password']),
        "approval_status": "pending"
    }
    
    try:
        inserted = sheets_repo.insert("users", new_user_dict)
        return {"message": "Registered. Awaiting approval.", "username": inserted.get('username')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {e}")

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user), db: any = Depends(get_db)):
    """
    Handle user logout and update attendance.
    """
    try:
        from app.services import attendance_service
        u_id = str(getattr(current_user, 'user_id', getattr(current_user, 'id', '')))
        res = attendance_service.mark_checkout(db=db, user_id=u_id)
        return {"message": "Logged out", "checkout": res}
    except Exception as e:
        print(f"Logout error: {e}")
        return {"message": "Logged out", "error": str(e)}
