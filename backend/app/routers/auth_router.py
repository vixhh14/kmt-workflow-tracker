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

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: any = Depends(get_db)):
    """
    Authenticate user and return JWT token using Google Sheets Backend.
    """
    from app.core.config import JWT_SECRET
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="Server security token missing")

    print(f"Login request: {credentials.username}")
    
    try:
        # Load all users from Sheets (cached)
        all_users = db.query(User).all()
        print(f"📊 Total users loaded: {len(all_users)}")
        
        # Manual case-insensitive and is_deleted filter
        user = next((u for u in all_users if str(u.username).lower() == credentials.username.lower() and not u.is_deleted), None)

        if not user:
            print(f"❌ User '{credentials.username}' not found or is deleted")
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        print(f"✅ User found: {user.username}")
        print(f"   Role: {user.role}")
        print(f"   Approval: {user.approval_status}")
        print(f"   Is Deleted: {user.is_deleted}")
        print(f"   Has password_hash: {bool(user.password_hash)}")
        if user.password_hash:
            print(f"   Hash length: {len(user.password_hash)}")
            print(f"   Hash preview: {user.password_hash[:30]}...")
        
        # Approval check
        user_role = (user.role or "operator").lower()
        if user_role != 'admin':
            status = str(user.approval_status or 'pending').lower()
            if status == 'pending':
                raise HTTPException(status_code=403, detail="Account awaiting admin approval")
            elif status == 'rejected':
                raise HTTPException(status_code=403, detail="Account registration rejected")
        
        # Password verification
        print(f"🔐 Verifying password...")
        if not user.password_hash:
            print(f"❌ No password hash stored!")
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        password_valid = verify_password(credentials.password, user.password_hash)
        print(f"   Password valid: {password_valid}")
        
        if not password_valid:
            print(f"❌ Password verification failed!")
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        
        # JWT Token
        token_data = {"sub": str(user.username), "user_id": str(user.user_id), "role": str(user_role)}
        access_token = create_access_token(data=token_data)
        
        # Mark Attendance (IST)
        try:
            from app.services import attendance_service
            attendance_service.mark_present(db=db, user_id=user.user_id)
        except Exception as e:
            print(f"⚠️ Attendance mark failed: {e}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "user_id": str(user.user_id),
                "username": str(user.username),
                "email": str(user.email or ""),
                "role": str(user_role),
                "full_name": str(user.full_name or user.username)
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
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "unit_id": current_user.unit_id,
        "machine_types": current_user.machine_types,
        "created_at": current_user.created_at,
        "contact_number": current_user.contact_number,
        "security_question": current_user.security_question
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
    
    # Check uniqueness
    if "username" in update_data and update_data["username"] != current_user.username:
        if any(u.username == update_data["username"] for u in all_users):
            raise HTTPException(status_code=400, detail="Username taken")
            
    if "email" in update_data and update_data["email"] != current_user.email:
        if any(u.email == update_data["email"] for u in all_users):
            raise HTTPException(status_code=400, detail="Email taken")

    # Update row
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.commit()
    return {"message": "Profile updated successfully"}

class ForgotPasswordRequest(BaseModel):
    username: str

@router.post("/get-security-question")
async def get_security_question(request: ForgotPasswordRequest, db: any = Depends(get_db)):
    """Get security question for a user (forgot password step 1)"""
    all_users = db.query(User).all()
    user = next((u for u in all_users if (str(u.username).lower() == request.username.lower() or str(u.email or "").lower() == request.username.lower()) and not u.is_deleted), None)
    
    if not user or not user.security_question:
        raise HTTPException(status_code=404, detail="Security question not set or user not found")
        
    return {"question": user.security_question}

class ResetPasswordRequest(BaseModel):
    username: str
    security_answer: str
    new_password: str

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: any = Depends(get_db)):
    """Reset password using security answer (forgot password step 2)"""
    all_users = db.query(User).all()
    user = next((u for u in all_users if (str(u.username).lower() == request.username.lower() or str(u.email or "").lower() == request.username.lower()) and not u.is_deleted), None)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if str(user.security_answer).lower() != request.security_answer.lower():
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
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    if request.new_password != request.confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    is_valid, errors = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors[0])
        
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.post("/signup")
async def signup(user_data: dict, db: any = Depends(get_db)):
    """
    Register new user.
    User will be in 'pending' status until admin approves.
    """
    # Basic Validation
    for field in ['username', 'password', 'email', 'full_name']:
        if not user_data.get(field):
            raise HTTPException(status_code=400, detail=f"{field} is required")

    all_users = db.query(User).all()
    if any(u.username == user_data['username'] for u in all_users):
        raise HTTPException(status_code=400, detail="Username exists")
    
    # Check if email already exists
    if user_data.get('email'):
        if any(u.email == user_data['email'] for u in all_users):
            raise HTTPException(status_code=400, detail="Email already exists")
    
    is_valid, errors = validate_password_strength(user_data['password'])
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors[0])
    
    new_user = User(
        user_id=str(uuid.uuid4()),
        username=user_data['username'],
        password_hash=hash_password(user_data['password']),
        email=user_data.get('email'),
        full_name=user_data.get('full_name'),
        role='operator',
        contact_number=user_data.get('contact_number'),
        address=user_data.get('address'), 
        approval_status='pending',
        created_at=get_current_time_ist().isoformat(),
        updated_at=get_current_time_ist().isoformat()
    )
    
    db.add(new_user)
    return {"message": "Registered. Awaiting approval.", "username": new_user.username}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user), db: any = Depends(get_db)):
    """
    Handle user logout.
    This is ONLY called when user clicks the LOGOUT button.
    Records check-out time in attendance.
    """
    try:
        from app.services import attendance_service
        res = attendance_service.mark_checkout(db=db, user_id=current_user.user_id)
        return {"message": "Logged out", "checkout": res}
    except Exception as e:
        return {"message": "Logged out", "error": str(e)}
