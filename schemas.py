from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

class UserBase(BaseModel):
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str
    security_question: str
    security_answer: str

class DoctorCreate(BaseModel):
    full_name: str
    gender: str
    doctor_id: str
    specialization: str
    experience: int
    qualification: str
    phone: str
    
class PatientCreate(BaseModel):
    full_name: str
    gender: str
    age: int
    blood_group: str
    phone: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
