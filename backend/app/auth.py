import hashlib
import os
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Manager credentials (in production, store in env vars)
MANAGER_NAME     = "Anil"
MANAGER_PASSWORD = "6472"

def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)

def verify_pin(pin: str, hashed: str) -> bool:
    return pwd_context.verify(pin, hashed)

def get_user_by_pin(db: Session, pin: str):
    users = db.query(User).filter(User.is_active == True).all()
    for user in users:
        if verify_pin(pin, user.pin_hash):
            return user
    return None

def create_user(db: Session, full_name: str, role: str, pin: str, phone: str = None):
    user = User(
        full_name=full_name,
        role=role,
        pin_hash=hash_pin(pin),
        phone=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_manager(password: str) -> bool:
    return password == MANAGER_PASSWORD
