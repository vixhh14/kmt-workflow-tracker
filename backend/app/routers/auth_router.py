from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
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
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    from app.core.config import JWT_SECRET
    
    if not JWT_SECRET:
        print("❌ CRITICAL: JWT_SECRET is not set in environment variables.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Security token missing"
        )

    start_time = time.time()
    print(f"Login request received for: {credentials.username}")
    
    try:
        # Find user by username
        # Use case-insensitive comparison and handle soft-delete
        t1 = time.time()
        try:
            user = db.query(User).filter(
                func.lower(User.username) == func.lower(credentials.username), 
                or_(User.is_deleted == False, User.is_deleted == None)
            ).first()
        except Exception as query_error:
            print(f"❌ Database query error during login: {query_error}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service temporarily unavailable"
            )
            
        print(f"Database query took: {time.time() - t1:.4f}s")
        
        if not user:
            print(f"Login failed: User '{credentials.username}' not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check approval status
        user_role = (user.role or "operator").lower()
        if user_role != 'admin':
            approval = getattr(user, 'approval_status', 'pending')
            if approval == 'pending':
                print(f"Login blocked: User '{user.username}' is pending approval")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account is awaiting approval by the admin.",
                )
            elif approval == 'rejected':
                print(f"Login blocked: User '{user.username}' was rejected")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account registration was rejected. Please contact admin.",
                )
        
        # Verify password existence
        if not user.password_hash:
            print(f"Login failed: User {user.username} has no password hash.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        t2 = time.time()
        try:
            is_valid = verify_password(credentials.password, user.password_hash)
        except Exception as e:
            print(f"❌ Error during password verification for {credentials.username}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal authentication error"
            )

        print(f"Password verification took: {time.time() - t2:.4f}s")
        
        if not is_valid:
            print(f"Login failed: Invalid password for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        t3 = time.time()
        try:
            token_data = {
                "sub": str(user.username or ""),
                "user_id": str(user.user_id or ""),
                "role": str(user_role)
            }
            access_token = create_access_token(data=token_data)
        except Exception as e:
            print(f"❌ Error creating access token for {credentials.username}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate authentication token"
            )
        print(f"Token creation took: {time.time() - t3:.4f}s")
        
        # Automatically mark user as present for today (Non-blocking)
        try:
            from app.services import attendance_service
            if hasattr(attendance_service, 'mark_present'):
                 attendance_result = attendance_service.mark_present(
                    db=db,
                    user_id=user.user_id,
                    ip_address=None
                )
                 if attendance_result.get("success"):
                     print(f"✅ Attendance marked for {user.username}")
                 else:
                     print(f"⚠️ Attendance marking failed: {attendance_result.get('message')}")
        except Exception as e:
            print(f"❌ Error marking attendance (non-blocking): {e}")
        
        print(f"✅ Login successful for {user.username} in {time.time() - start_time:.4f}s")
        
        # Return token and user info - ensure all fields are explicitly string converted if needed
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
    except HTTPException:
        # Re-raise HTTP exceptions to maintain correct status codes
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ UNEXPECTED Login error for user '{credentials.username}': {str(e)}")
        print(f"❌ Full traceback:\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed due to unexpected error: {str(e)}"
        )


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
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    update_data = updates.dict(exclude_none=True)
    
    # Validation for unique fields
    if "username" in update_data and update_data["username"] != current_user.username:
        if db.query(User).filter(func.lower(User.username) == func.lower(update_data["username"]), or_(User.is_deleted == False, User.is_deleted == None)).first():
            raise HTTPException(status_code=400, detail="Username already taken")
            
    if "email" in update_data and update_data["email"] != current_user.email:
        if db.query(User).filter(func.lower(User.email) == func.lower(update_data["email"]), or_(User.is_deleted == False, User.is_deleted == None)).first():
            raise HTTPException(status_code=400, detail="Email already taken")

    # Update fields
    for key, value in update_data.items():
        # Specifically hash the security answer if provided (optional but safer)
        # For now, just store as plain text as it's a simple reset flow
        setattr(current_user, key, value)
        
    from app.core.time_utils import get_current_time_ist
    current_user.updated_at = get_current_time_ist()
    
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully", "user": {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "contact_number": current_user.contact_number
    }}

class ForgotPasswordRequest(BaseModel):
    username: str

@router.post("/get-security-question")
async def get_security_question(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Get security question for a user (forgot password step 1)"""
    user = db.query(User).filter(
        or_(func.lower(User.username) == func.lower(request.username), func.lower(User.email) == func.lower(request.username)),
        or_(User.is_deleted == False, User.is_deleted == None)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.security_question:
        raise HTTPException(status_code=400, detail="No security question set for this user. Please contact admin.")
        
    return {"question": user.security_question}

class ResetPasswordRequest(BaseModel):
    username: str
    security_answer: str
    new_password: str

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using security answer (forgot password step 2)"""
    user = db.query(User).filter(
        or_(func.lower(User.username) == func.lower(request.username), func.lower(User.email) == func.lower(request.username)),
        or_(User.is_deleted == False, User.is_deleted == None)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.security_answer or user.security_answer.lower() != request.security_answer.lower():
        raise HTTPException(status_code=400, detail="Incorrect security answer")
        
    # Validate password strength
    is_valid, errors = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors[0])
        
    # Reset
    user.password_hash = hash_password(request.new_password)
    from app.core.time_utils import get_current_time_ist
    user.updated_at = get_current_time_ist()
    
    db.commit()
    return {"message": "Password reset successfully"}

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change password for logged in user"""
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Check match
    if request.new_password != request.confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
        
    # Validate strength
    is_valid, errors = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=errors[0] if errors else "Password does not meet security requirements"
        )
        
    # Update
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/signup")
async def signup(user_data: dict, db: Session = Depends(get_db)):
    """
    Register new user.
    User will be in 'pending' status until admin approves.
    """
    from app.core.auth_utils import hash_password
    import uuid
    
    # Required fields validation
    required_fields = ['username', 'password', 'email', 'full_name', 'contact_number']
    for field in required_fields:
        if not user_data.get(field):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field {field} is required"
            )

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data['username']).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    if user_data.get('email'):
        existing_email = db.query(User).filter(User.email == user_data['email']).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Validate password strength
    is_valid, errors = validate_password_strength(user_data.get('password', ''))
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0] if errors else "Password does not meet security requirements"
        )
    
    # Create new user
    new_user = User(
        user_id=str(uuid.uuid4()),
        username=user_data['username'],
        password_hash=hash_password(user_data['password']),
        email=user_data.get('email'),
        full_name=user_data.get('full_name'),
        role='operator', # Default role
        contact_number=user_data.get('contact_number'),
        # Map 'contact' from form to address if provided, or just keep it separate if needed.
        # Assuming 'Contact' in request meant 'Contact Number', but since both are listed, 
        # I'll check if 'address' is passed or if 'contact' is passed.
        address=user_data.get('address'), 
        approval_status='pending'
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create approval record
    from app.models.models_db import UserApproval
    new_approval = UserApproval(
        user_id=new_user.user_id,
        status='pending'
    )
    db.add(new_approval)
    db.commit()
    
    return {
        "message": "User registered successfully. Pending admin approval.",
        "user_id": new_user.user_id,
        "username": new_user.username
    }

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Handle user logout.
    This is ONLY called when user clicks the LOGOUT button.
    Records check-out time in attendance.
    """
    try:
        from app.services import attendance_service
        
        # Mark checkout in attendance
        checkout_result = attendance_service.mark_checkout(
            db=db,
            user_id=current_user.user_id
        )
        
        if checkout_result.get("success"):
            print(f"✅ Checkout recorded for {current_user.username}: {checkout_result.get('message')}")
        else:
            print(f"⚠️ Checkout failed: {checkout_result.get('message')}")
        
        return {
            "message": "Logged out successfully",
            "checkout": checkout_result
        }
    except Exception as e:
        print(f"❌ Error during logout: {e}")
        # Don't fail logout if checkout fails
        return {
            "message": "Logged out successfully",
            "checkout": {
                "success": False,
                "error": str(e)
            }
        }

