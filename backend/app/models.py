from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    full_name  = Column(String, nullable=False)
    role       = Column(String, nullable=False)
    pin_hash   = Column(String, nullable=False, unique=True)
    phone      = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active  = Column(Boolean, default=True)

    attendance = relationship("Attendance", back_populates="user")


class Attendance(Base):
    __tablename__ = "attendance"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    date             = Column(Date, nullable=False)
    clock_in         = Column(DateTime, nullable=True)
    clock_out        = Column(DateTime, nullable=True)
    hours_worked     = Column(Float, nullable=True)
    auto_clocked_out = Column(Boolean, default=False)

    user = relationship("User", back_populates="attendance")
