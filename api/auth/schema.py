from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserList(BaseModel):
    # id: int = None
    email: str
    username: str
    # created_at: Optional[datetime] = None
    status: str = None
    password: str
    role: str


# class UserOutput()


class UserCreate(BaseModel):
    id: int 
    email: str
    username: str
    password: str
    created_at: Optional[datetime] = None
    # hashed_password: Optional[str] = None


class User(BaseModel):
    id: int = None
    username: str
    password: str
    email: str
    status: str
    created_at: datetime
    role: str

class ResetUser(BaseModel):
    id: int = None
    email: str
    reset_code: str
    status: str
    expired: datetime
    hashed_otp: str



class ForgotPassword(BaseModel):
    email: str


class ResetPassword(BaseModel):
    reset_password_token: str
    new_password: str
    confirm_password: str


class UserLogin(BaseModel):
    username: str
    password: str


class VerificationDetails(BaseModel):
    username: str
    otp: str


class UserReturn(BaseModel):
    id: int
    username: str
    email: str
    status: str
    created_at: datetime
    updated_at: datetime
    role: str   
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None  # Ensures valid email
    username: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None


