from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Attendance, User
from app.schemas import ClockRequest
from app.tz import store_now, store_today

router = APIRouter()

def calc_hours(clock_in: datetime, clock_out: datetime) -> float:
    delta = clock_out - clock_in
    return round(delta.total_seconds() / 3600, 2)

@router.post("/clock-in")
def clock_in(data: ClockRequest, db: Session = Depends(get_db)):
    today = store_today()
    existing = db.query(Attendance).filter(
        Attendance.user_id == data.user_id,
        Attendance.date == today
    ).first()
    if existing:
        if existing.clock_out:
            raise HTTPException(status_code=400, detail="You have already completed your shift today.")
        raise HTTPException(status_code=400, detail="Already clocked in today.")
    record = Attendance(
        user_id=data.user_id,
        date=today,
        clock_in=store_now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"message": "Clocked in", "clock_in": record.clock_in, "id": record.id}

@router.post("/clock-out")
def clock_out(data: ClockRequest, db: Session = Depends(get_db)):
    today = store_today()
    record = db.query(Attendance).filter(
        Attendance.user_id == data.user_id,
        Attendance.date == today
    ).first()
    if not record:
        raise HTTPException(status_code=400, detail="You haven't clocked in today.")
    if record.clock_out:
        raise HTTPException(status_code=400, detail="Already clocked out.")
    record.clock_out = store_now()
    record.hours_worked = calc_hours(record.clock_in, record.clock_out)
    db.commit()
    db.refresh(record)
    return {"message": "Clocked out", "clock_out": record.clock_out, "hours_worked": record.hours_worked}

@router.get("/today/{user_id}")
def today_status(user_id: int, db: Session = Depends(get_db)):
    today = store_today()
    record = db.query(Attendance).filter(
        Attendance.user_id == user_id,
        Attendance.date == today
    ).first()
    if not record:
        return {"status": "not_clocked_in", "clock_in": None, "clock_out": None}
    if record.clock_out:
        return {
            "status": "clocked_out",
            "clock_in": record.clock_in,
            "clock_out": record.clock_out,
            "hours_worked": record.hours_worked,
        }
    return {"status": "clocked_in", "clock_in": record.clock_in, "clock_out": None}

@router.get("/monthly/{user_id}")
def monthly_report(user_id: int, year: int, month: int, db: Session = Depends(get_db)):
    from sqlalchemy import extract
    records = db.query(Attendance).filter(
        Attendance.user_id == user_id,
        extract("year",  Attendance.date) == year,
        extract("month", Attendance.date) == month,
    ).order_by(Attendance.date).all()

    rows = []
    total_hours = 0.0
    for r in records:
        h = r.hours_worked or 0
        total_hours += h
        rows.append({
            "date": r.date,
            "clock_in": r.clock_in,
            "clock_out": r.clock_out,
            "hours_worked": r.hours_worked,
            "auto_clocked_out": r.auto_clocked_out,
        })
    return {
        "records": rows,
        "total_hours": round(total_hours, 2),
        "days_worked": len([r for r in rows if r["clock_in"]]),
    }
