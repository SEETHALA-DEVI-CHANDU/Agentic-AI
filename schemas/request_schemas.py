from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1)
    school: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)

class VisualRequest(BaseModel):
    description: str

class AudioRequest(BaseModel):
    transcribed_text: str

class AskLearnRequest(BaseModel):
    question: str
    grade: int = Field(..., ge=1, le=12)
    difficulty: str

class PlanWeekRequest(BaseModel):
    grade: int = Field(..., ge=1, le=12)
    subject: str
    chapter: str

class FeedbackRequest(BaseModel):
    feedback_text: str