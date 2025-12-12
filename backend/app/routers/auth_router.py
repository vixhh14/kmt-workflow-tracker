from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models.auth_model import LoginRequest, LoginResponse, ChangePasswordRequest
from app.core.auth_utils import verify_password, create_access_token, hash_password
from app.core.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.models_db import User
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
    import time
    start_time = time.time()
    print(f"Login request received for: {credentials.username}")
    
    try:
        # Find user by username in SQLite
        t1 = time.time()
        user = db.query(User).filter(User.username == credentials.username).first()
        print(f"Database query took: {time.time() - t1:.4f}s")
        
        if not user:
            print("User not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check approval status
        # Admin bypasses approval check (optional, but good for safety)
        if user.role != 'admin':
            if hasattr(user, 'approval_status'):
                if user.approval_status == 'pending':
                    print("User pending approval")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Your account is awaiting approval by the admin.",
                    )
                elif user.approval_status == 'rejected':
                    print("User rejected")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Your account registration was rejected. Please contact admin.",
                    )
        
        # Verify password
        t2 = time.time()
        is_valid = verify_password(credentials.password, user.password_hash)
        print(f"Password verification took: {time.time() - t2:.4f}s")
        
        if not is_valid:
            print(f"Invalid password for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        t3 = time.time()
        access_token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.user_id,
                "role": user.role
            }
        )
        print(f"Token creation took: {time.time() - t3:.4f}s")
        
        # Automatically mark user as present for today
        try:
            from app.services import attendance_service
            t4 = time.time()
            attendance_result = attendance_service.mark_present(
                db=db,
                user_id=user.user_id,
                ip_address=None  # Could get from request if needed
            )
            print(f"Attendance marking took: {time.time() - t4:.4f}s")
            if attendance_result.get("success"):
                print(f"✅ Attendance marked for {user.username}: {attendance_result.get('message')}")
            else:
                print(f"⚠️ Attendance marking failed: {attendance_result.get('message')}")
        except Exception as e:
            print(f"❌ Error marking attendance: {e}")
            # Don't fail login if attendance fails
        
        print(f"Total login time: {time.time() - start_time:.4f}s")
        
        # Return token and user info
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Login error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
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
        "created_at": current_user.created_at
    }

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

