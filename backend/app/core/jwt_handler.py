from datetime import datetime, timedelta
from jose import jwt
from app.core.config import JWT_SECRET, JWT_ALGORITHM

def create_access_token(subject: str, role: str, expires_minutes: int = None):
    expires_minutes = expires_minutes or 60
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode = {"sub": subject, "role": role, "exp": expire}
    encoded = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None
