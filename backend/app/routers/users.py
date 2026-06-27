from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import RegisterRequest, LoginRequest
from app.auth import create_user, get_user_by_pin, verify_manager
from app.models import User

router = APIRouter()

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if len(data.pin) != 4 or not data.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits.")
    # Check PIN uniqueness
    existing = get_user_by_pin(db, data.pin)
    if existing:
        raise HTTPException(status_code=400, detail="PIN already in use. Choose another.")
    user = create_user(db, data.full_name, data.role, data.pin, data.phone)
    return {"message": "Registered successfully", "id": user.id, "name": user.full_name}

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # Manager check
    if verify_manager(data.pin):
        return {"id": 0, "name": "Anil", "role": "Manager", "is_manager": True}
    user = get_user_by_pin(db, data.pin)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid PIN. If new, please register first.")
    return {"id": user.id, "name": user.full_name, "role": user.role, "is_manager": False}

@router.get("/list")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_active == True).all()
    return [{"id": u.id, "name": u.full_name, "role": u.role, "created_at": u.created_at} for u in users]
