from pydantic import BaseModel, field_validator

class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def trim_username(cls, v: str) -> str:
        return v.strip()

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class SecurityQuestionRequest(BaseModel):
    username: str

class PasswordResetRequest(BaseModel):
    username: str
    security_answer: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str
