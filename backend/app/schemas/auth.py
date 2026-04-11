from pydantic import BaseModel, EmailStr
from uuid import UUID

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class UserResponse(BaseModel):
    id: UUID
    store_id: UUID
    name: str
    email: EmailStr
    role: str
    
    class Config:
        from_attributes = True
