"""
Store closing times and automatic clock-out of shifts left open.

Rule: a shift still open after its date's closing time is closed AT the closing time
(not at whatever moment the job happens to run). The job is a catch-up sweep, so shifts
are still closed correctly if the server was asleep or restarting at closing time.

Shifts started after closing time (e.g. a late clock-in) are left open until the end of
that day so the employee can still clock out normally; if they never do, the shift is
closed at its clock-in time (0 hours) and flagged auto, for the manager to review,
rather than inventing hours.
"""
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models import Attendance

# weekday(): 0=Mon ... 6=Sun - all times are store-local (see app.tz.STORE_TZ)
CLOSING_TIMES = {
    0: time(22, 0),   # Monday    10:00 PM
    1: time(22, 0),   # Tuesday   10:00 PM
    2: time(22, 0),   # Wednesday 10:00 PM
    3: time(22, 0),   # Thursday  10:00 PM
    4: time(23, 0),   # Friday    11:00 PM
    5: time(23, 0),   # Saturday  11:00 PM
    6: time(21, 10),  # Sunday     9:10 PM
}


def closing_datetime(d: date) -> datetime:
    return datetime.combine(d, CLOSING_TIMES[d.weekday()])


def auto_close_open_shifts(db: Session, now: datetime) -> int:
    """Close every open shift whose closing time has passed. Returns how many were closed."""
    open_records = (
        db.query(Attendance)
        .filter(
            Attendance.clock_in != None,
            Attendance.clock_out == None,
            Attendance.date <= now.date(),
        )
        .all()
    )

    closed = 0
    for rec in open_records:
        close_at = closing_datetime(rec.date)
        if rec.clock_in >= close_at:
            # Clocked in after closing: wait until the day is over, then close with 0 hours.
            if now < datetime.combine(rec.date + timedelta(days=1), time(0, 0)):
                continue
            close_at = rec.clock_in
        elif now < close_at:
            continue

        rec.clock_out = close_at
        rec.hours_worked = round((rec.clock_out - rec.clock_in).total_seconds() / 3600, 2)
        rec.auto_clocked_out = True
        closed += 1

    if closed:
        db.commit()
    return closed
