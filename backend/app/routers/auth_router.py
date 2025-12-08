from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models.auth_model import LoginRequest, LoginResponse, SecurityQuestionRequest, PasswordResetRequest, ChangePasswordRequest
from app.core.auth_utils import verify_password, create_access_token, hash_password
from app.core.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.models_db import User
from app.core.password_validation import validate_password_strength

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

@router.post("/get-security-question")
async def get_security_question(request: SecurityQuestionRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.security_question:
        raise HTTPException(status_code=400, detail="No security question set for this user")
        
    return {"question": user.security_question}

@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.security_answer:
        raise HTTPException(status_code=400, detail="No security answer set for this user")
        
    # Verify answer (case-insensitive)
    if user.security_answer.lower().strip() != request.security_answer.lower().strip():
        raise HTTPException(status_code=400, detail="Incorrect security answer")
    
    # Validate new password strength
    is_valid, errors = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0] if errors else "Password does not meet security requirements"
        )
        
    # Update password
    user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    Uses local SQLite database for instant login.
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
        if hasattr(user, 'approval_status') and user.approval_status == 'pending':
            print("User pending approval")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is pending admin approval. Please wait for approval before logging in.",
            )
        
        if hasattr(user, 'approval_status') and user.approval_status == 'rejected':
            print("User rejected")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account registration was rejected. Please contact admin for more information.",
            )
        
        # Verify password
        t2 = time.time()
        is_valid = verify_password(credentials.password, user.password_hash)
        print(f"Password verification took: {time.time() - t2:.4f}s")
        
        if not is_valid:
            print(f"Invalid password for user {user.username}")
            print(f"Stored hash: {user.password_hash}")
            # Verify if hash looks like bcrypt
            if not user.password_hash.startswith('$2b$'):
                print("CRITICAL: Stored hash does not look like a valid bcrypt hash!")
            
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
        
        # Record Attendance
        try:
            from app.models.models_db import Attendance
            from datetime import datetime
            today_str = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Check if already marked for today
            existing_attendance = db.query(Attendance).filter(
                Attendance.user_id == user.user_id,
                Attendance.date == today_str
            ).first()
            
            if not existing_attendance:
                new_attendance = Attendance(
                    user_id=user.user_id,
                    date=today_str,
                    status='present',
                    # ip_address=request.client.host # Requires Request object, skipping for now
                )
                db.add(new_attendance)
                db.commit()
                print(f"Attendance marked for {user.username}")
        except Exception as e:
            print(f"Error marking attendance: {e}")
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
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
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
    Register new user with onboarding data.
    User will be in 'pending' status until admin approves.
    """
    from app.core.auth_utils import hash_password
    import uuid
    
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
        role='operator', # Enforce operator role for self-signup
        date_of_birth=user_data.get('date_of_birth'),
        address=user_data.get('address'),
        contact_number=user_data.get('contact_number'),
        unit_id=user_data.get('unit_id'),
        approval_status='pending'
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Add skills if present
    if 'skills' in user_data and isinstance(user_data['skills'], list):
        from app.models.models_db import UserMachine
        for skill in user_data['skills']:
            # skill should be {'machine_id': '...', 'skill_level': '...'}
            if skill.get('machine_id'):
                new_skill = UserMachine(
                    user_id=new_user.user_id,
                    machine_id=skill.get('machine_id'),
                    skill_level=skill.get('skill_level', 'intermediate')
                )
                db.add(new_skill)
        db.commit()
    
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
