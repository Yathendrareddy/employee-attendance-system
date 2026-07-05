from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

class RegisterRequest(BaseModel):
    full_name: str
    role: str
    pin: str
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    pin: str

class ManagerLoginRequest(BaseModel):
    password: str

class ClockRequest(BaseModel):
    user_id: int

class EditAttendanceRequest(BaseModel):
    clock_in: Optional[str] = None   # "HH:MM"
    clock_out: Optional[str] = None  # "HH:MM"

class ManualAttendanceRequest(BaseModel):
    employee_ids: List[int]
    date: str                        # "YYYY-MM-DD"
    clock_in: Optional[str] = None   # "HH:MM"
    clock_out: Optional[str] = None  # "HH:MM"
    manager_id: Optional[int] = None

class ClockOutAllRequest(BaseModel):
    manager_id: Optional[int] = None

class AttendanceRecord(BaseModel):
    id: int
    date: date
    clock_in: Optional[datetime]
    clock_out: Optional[datetime]
    hours_worked: Optional[float]
    auto_clocked_out: bool

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    full_name: str
    role: str
    phone: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
