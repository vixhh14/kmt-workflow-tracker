# app/models/auth_model.py
from pydantic import BaseModel

# Register Request Model
class RegisterUser(BaseModel):
    username: str
    password: str
    role: str = "operator"
    full_name: str | None = None


# Login Request Model
class LoginRequest(BaseModel):
    username: str
    password: str


# JWT Token Response
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
