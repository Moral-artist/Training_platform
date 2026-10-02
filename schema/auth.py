from pydantic import BaseModel, EmailStr, Field
from enum import Enum

class CharacterEnum(str, Enum):
    ENGINEER = 'engineer'
    OPERATOR = 'operator'
    SHIFTLEADER = 'shiftleader'

class RegisterRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    character: CharacterEnum | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(
        min_length=8,
        max_length=128
    )

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"