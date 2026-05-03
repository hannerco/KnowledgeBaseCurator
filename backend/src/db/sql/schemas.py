from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)
    
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    sender: str = Field(..., pattern="^(user|system)$")  # Ensure sender is either 'user' or 'assistant'
    
class MessageResponse(BaseModel):
    id: int
    user_id: int
    content: str
    timestamp: datetime
    sender: str
    