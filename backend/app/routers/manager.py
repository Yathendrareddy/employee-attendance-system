from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date, datetime
import csv, io
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.models import User, Attendance
from app.schemas import EditAttendanceRequest

router = APIRouter()

@router.get("/employees")
def all_employees(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_active == True).all()
    result = []
    for u in users:
        today = date.today()
        today_rec = next((a for a in u.attendance if a.date == today), None)
        status = "not_clocked_in"
        if today_rec:
            status = "clocked_out" if today_rec.clock_out else "clocked_in"
        result.append({
            "id": u.id,
            "name": u.full_name,
            "role": u.role,
            "phone": u.phone,
            "created_at": u.created_at,
            "today_status": status,
            "clock_in": today_rec.clock_in if today_rec else None,
        })
    return result

@router.get("/report")
def manager_report(year: int, month: int, db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_active == True).all()
    result = []
    for u in users:
        records = db.query(Attendance).filter(
            Attendance.user_id == u.id,
            extract("year",  Attendance.date) == year,
            extract("month", Attendance.date) == month,
        ).order_by(Attendance.date).all()

        total_hours  = sum(r.hours_worked or 0 for r in records)
        days_worked  = len([r for r in records if r.clock_in])
        result.append({
            "id": u.id,
            "name": u.full_name,
            "role": u.role,
            "days_worked": days_worked,
            "total_hours": round(total_hours, 2),
            "records": [{
                "id": r.id,
                "date": r.date,
                "clock_in": r.clock_in,
                "clock_out": r.clock_out,
                "hours_worked": r.hours_worked,
                "auto_clocked_out": r.auto_clocked_out,
            } for r in records],
        })
    return result

@router.get("/export-csv")
def export_csv(year: int, month: int, db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_active == True).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee", "Role", "Date", "Clock In", "Clock Out", "Hours", "Auto"])

    for u in users:
        records = db.query(Attendance).filter(
            Attendance.user_id == u.id,
            extract("year",  Attendance.date) == year,
            extract("month", Attendance.date) == month,
        ).order_by(Attendance.date).all()
        for r in records:
            writer.writerow([
                u.full_name, u.role, r.date,
                r.clock_in.strftime("%H:%M") if r.clock_in else "",
                r.clock_out.strftime("%H:%M") if r.clock_out else "",
                r.hours_worked or "",
                "Yes" if r.auto_clocked_out else "No",
            ])

    output.seek(0)
    filename = f"attendance_{year}_{month:02d}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.delete("/employees/{user_id}")
def delete_employee(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found.")
    user.is_active = False
    db.commit()
    return {"message": f"{user.full_name} removed."}

@router.patch("/attendance/{record_id}")
def edit_attendance(record_id: int, data: EditAttendanceRequest, db: Session = Depends(get_db)):
    record = db.query(Attendance).filter(Attendance.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found.")

    def parse_time(t: str) -> datetime:
        h, m = map(int, t.split(":"))
        return datetime(record.date.year, record.date.month, record.date.day, h, m)

    if data.clock_in is not None:
        record.clock_in = parse_time(data.clock_in)
    if data.clock_out is not None:
        record.clock_out = parse_time(data.clock_out)

    if record.clock_in and record.clock_out:
        if record.clock_out <= record.clock_in:
            raise HTTPException(status_code=400, detail="Clock out must be after clock in.")
        record.hours_worked = round((record.clock_out - record.clock_in).total_seconds() / 3600, 2)
        record.auto_clocked_out = False

    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "date": record.date,
        "clock_in": record.clock_in,
        "clock_out": record.clock_out,
        "hours_worked": record.hours_worked,
        "auto_clocked_out": record.auto_clocked_out,
    }

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    today = date.today()
    users = db.query(User).filter(User.is_active == True).all()
    working_now = 0
    today_hours = 0.0
    for u in users:
        rec = next((a for a in u.attendance if a.date == today), None)
        if rec and rec.clock_in and not rec.clock_out:
            working_now += 1
        if rec and rec.hours_worked:
            today_hours += rec.hours_worked
    return {
        "total_employees": len(users),
        "working_now": working_now,
        "today_hours": round(today_hours, 2),
    }
