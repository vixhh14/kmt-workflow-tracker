from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.database import get_db
from app.core.auth_utils import decode_access_token
from app.models.models_db import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

from app.core.normalizer import normalize_user_row, safe_bool, safe_str

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: any = Depends(get_db)
):
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: no user found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 1. Fetch ALL users (safer than DB filtering with loose types)
    try:
        all_users = db.query(User).all()
        
        # 2. Manual Filter (Handles "TRUE"/"1"/True mismatch)
        user = None
        for u in all_users:
            u_dict = u.dict() if hasattr(u, "dict") else u.__dict__
            
            # Check username match
            if safe_str(u_dict.get('username')) != username:
                continue
                
            # Check is_deleted (Skip if True)
            if safe_bool(u_dict.get('is_deleted'), False):
                continue
                
            # Check active (Skip if False)
            if not safe_bool(u_dict.get('active'), True):
                continue
                
            user = u
            break
            
        if not user:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        # 3. Normalize User Object (Ensure all fields exist)
        # We wrap it back into a standard object or return dict, 
        # but let's modify the object in-place or trust the attributes are accessible?
        # Best is to return the ORM object but ensure we access it safely later.
        # However, for 'user.role' checks in dependencies, we need it safe.
        
        # Let's attach normalized values to the object to be safe
        u_dict = user.dict() if hasattr(user, "dict") else user.__dict__
        normalized = normalize_user_row(u_dict)
        
        # Patch the user object with normalized values so getattr(user, 'role') works safely
        for k, v in normalized.items():
            setattr(user, k, v)
            
        return user

    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


# -------------------------
# NEW FUNCTION (Fixes Render Error)
# General active user check
# -------------------------
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # You can expand this (block disabled users, deleted users, etc.)
    return current_user


# -------------------------
# Admin permission check
# -------------------------
async def get_current_active_admin(current_user: User = Depends(get_current_active_user)):
    if str(getattr(current_user, 'role', '')).lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges"
        )
    return current_user
