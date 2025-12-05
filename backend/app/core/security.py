from datetime import datetime, timedelta
from jose import jwt
from app.core.config import JWT_SECRET, JWT_ALGORITHM

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode = data.copy()
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
