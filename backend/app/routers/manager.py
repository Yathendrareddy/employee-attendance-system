from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import datetime
import csv, io, logging
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.models import User, Attendance
from app.schemas import EditAttendanceRequest, ManualAttendanceRequest, ClockOutAllRequest
from app.tz import store_now, store_today

router = APIRouter()

audit_logger = logging.getLogger("attendance_audit")
audit_logger.setLevel(logging.INFO)
if not audit_logger.handlers:
    _audit_handler = logging.StreamHandler()
    _audit_handler.setFormatter(logging.Formatter("%(asctime)s AUDIT %(message)s"))
    audit_logger.addHandler(_audit_handler)
    audit_logger.propagate = False


def _parse_time_on_date(d, t: str) -> datetime:
    try:
        h, m = map(int, t.split(":"))
        return datetime(d.year, d.month, d.day, h, m)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"Invalid time format: {t!r}. Expected HH:MM.")


def _apply_times(record: Attendance, clock_in: str = None, clock_out: str = None):
    """Set clock_in/out on a record from 'HH:MM' strings and recompute hours. Shared by
    the single-record edit endpoint and the manager manual-entry/bulk endpoint."""
    if clock_in is not None:
        record.clock_in = _parse_time_on_date(record.date, clock_in)
    if clock_out is not None:
        record.clock_out = _parse_time_on_date(record.date, clock_out)

    if record.clock_in and record.clock_out:
        if record.clock_out <= record.clock_in:
            raise HTTPException(status_code=400, detail="Clock out must be after clock in.")
        record.hours_worked = round((record.clock_out - record.clock_in).total_seconds() / 3600, 2)
        record.auto_clocked_out = False

@router.get("/employees")
def all_employees(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_active == True).all()
    result = []
    for u in users:
        today = store_today()
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

    _apply_times(record, data.clock_in, data.clock_out)

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

@router.post("/attendance/manual")
def manual_attendance(data: ManualAttendanceRequest, db: Session = Depends(get_db)):
    """Manager-only manual clock in/out entry and editing, for one or many employees at once.
    Creates a record if none exists for that employee/date (manual entry), or updates it if one
    does (edit) - the same code path covers both single and bulk operations."""
    if not data.employee_ids:
        raise HTTPException(status_code=400, detail="Select at least one employee.")
    if data.clock_in is None and data.clock_out is None:
        raise HTTPException(status_code=400, detail="Provide a clock in or clock out time.")

    try:
        rec_date = datetime.strptime(data.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date. Expected YYYY-MM-DD.")

    results = []
    for emp_id in data.employee_ids:
        user = db.query(User).filter(User.id == emp_id, User.is_active == True).first()
        if not user:
            continue

        record = db.query(Attendance).filter(
            Attendance.user_id == emp_id, Attendance.date == rec_date
        ).first()
        if record is None:
            record = Attendance(user_id=emp_id, date=rec_date)
            db.add(record)
            old_in = old_out = None
        else:
            old_in, old_out = record.clock_in, record.clock_out

        # A clock-in with no clock-out means the employee is starting a fresh shift now -
        # clear any stale clock-out left over from a prior entry so status shows "working".
        if data.clock_in is not None and data.clock_out is None and record.clock_out is not None:
            record.clock_out = None
            record.hours_worked = None
            record.auto_clocked_out = False

        _apply_times(record, data.clock_in, data.clock_out)
        db.flush()

        if data.clock_in is not None:
            audit_logger.info(
                "action=%s manager_id=%s employee_id=%s date=%s old=%s new=%s",
                "edit_clock_in" if old_in is not None else "manual_clock_in",
                data.manager_id, emp_id, rec_date, old_in, record.clock_in,
            )
        if data.clock_out is not None:
            audit_logger.info(
                "action=%s manager_id=%s employee_id=%s date=%s old=%s new=%s",
                "edit_clock_out" if old_out is not None else "manual_clock_out",
                data.manager_id, emp_id, rec_date, old_out, record.clock_out,
            )

        results.append({
            "employee_id": emp_id,
            "name": user.full_name,
            "id": record.id,
            "date": record.date,
            "clock_in": record.clock_in,
            "clock_out": record.clock_out,
            "hours_worked": record.hours_worked,
            "auto_clocked_out": record.auto_clocked_out,
        })

    db.commit()
    return results

@router.post("/attendance/clock-out-all")
def clock_out_all(data: ClockOutAllRequest, db: Session = Depends(get_db)):
    """Manager-only bulk action: clock out every employee actually clocked in right now
    (today's open records with a clock-in already set, regardless of role)."""
    now = store_now()
    today = store_today()
    open_records = db.query(Attendance).filter(
        Attendance.date == today,
        Attendance.clock_out == None,
        Attendance.clock_in != None,
    ).all()

    results = []
    for record in open_records:
        record.clock_out = now
        if record.clock_in < record.clock_out:
            record.hours_worked = round((record.clock_out - record.clock_in).total_seconds() / 3600, 2)
        record.auto_clocked_out = True

        audit_logger.info(
            "action=%s manager_id=%s employee_id=%s date=%s old=%s new=%s",
            "bulk_clock_out", data.manager_id, record.user_id, today, None, record.clock_out,
        )
        results.append({
            "employee_id": record.user_id,
            "id": record.id,
            "clock_out": record.clock_out,
            "hours_worked": record.hours_worked,
        })

    db.commit()
    return {"clocked_out": len(results), "records": results}

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    today = store_today()
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
