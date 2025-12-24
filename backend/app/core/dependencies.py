from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth_utils import decode_access_token
from app.models.models_db import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# -------------------------
# Base Authentication: Check JWT and return logged-in user
# -------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
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
    
    user = db.query(User).filter(User.username == username, User.is_deleted == False).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


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
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges"
        )
    return current_user
