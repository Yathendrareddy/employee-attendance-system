"""
Run this once to add demo employees to the database.
Usage: python seed.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import SessionLocal, engine, Base
from app import models
from app.auth import create_user
from datetime import datetime, date, timedelta
import random

Base.metadata.create_all(bind=engine)

EMPLOYEES = [
    {"full_name": "Sara Ahmed",   "role": "Barista",    "pin": "1111", "phone": "050-111-0001"},
    {"full_name": "Ravi Kumar",   "role": "Chef",        "pin": "2222", "phone": "050-222-0002"},
    {"full_name": "Nadia Hassan", "role": "Cashier",     "pin": "3333", "phone": "050-333-0003"},
    {"full_name": "Tom Clarke",   "role": "Supervisor",  "pin": "4444", "phone": "050-444-0004"},
]

SHIFTS = [
    ("09:00", "17:00"), ("10:00", "18:30"),
    ("08:30", "16:00"), ("12:00", "20:00"), ("14:00", "22:00"),
]

CLOSING = {0:22, 1:22, 2:22, 3:22, 4:23, 5:23, 6:21}
CLOSING_MIN = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:30}

def calc_hours(ci, co):
    delta = co - ci
    return round(delta.total_seconds() / 3600, 2)

db = SessionLocal()

# Create employees
created = []
for e in EMPLOYEES:
    existing = None
    from app.auth import get_user_by_pin
    existing = get_user_by_pin(db, e["pin"])
    if not existing:
        user = create_user(db, e["full_name"], e["role"], e["pin"], e["phone"])
        created.append(user)
        print(f"  ✓ Created: {user.full_name} (PIN: {e['pin']})")
    else:
        created.append(existing)
        print(f"  ⚠ Already exists: {existing.full_name}")

# Seed attendance for current month
today = date.today()
for user_idx, user in enumerate(created):
    for day_offset in range(1, today.day):
        d = date(today.year, today.month, day_offset)
        if d.weekday() == 6:   # skip Sundays
            continue
        if random.random() < 0.1:  # 10% absent
            continue
        shift = SHIFTS[(day_offset + user_idx) % len(SHIFTS)]
        ci_h, ci_m = map(int, shift[0].split(":"))
        co_h, co_m = map(int, shift[1].split(":"))
        auto_out   = random.random() < 0.07

        clock_in  = datetime(d.year, d.month, d.day, ci_h, ci_m)
        if auto_out:
            dow = d.weekday()
            clock_out = datetime(d.year, d.month, d.day, CLOSING[dow], CLOSING_MIN[dow])
        else:
            clock_out = datetime(d.year, d.month, d.day, co_h, co_m)

        exists = db.query(models.Attendance).filter(
            models.Attendance.user_id == user.id,
            models.Attendance.date    == d
        ).first()
        if exists:
            continue

        rec = models.Attendance(
            user_id=user.id, date=d,
            clock_in=clock_in, clock_out=clock_out,
            hours_worked=calc_hours(clock_in, clock_out),
            auto_clocked_out=auto_out,
        )
        db.add(rec)

db.commit()
db.close()
print("\n✅ Seed complete!")
print("\nDemo logins:")
print("  Sara Ahmed   → PIN: 1111")
print("  Ravi Kumar   → PIN: 2222")
print("  Nadia Hassan → PIN: 3333")
print("  Tom Clarke   → PIN: 4444")
print("  Manager Anil → PIN: 6472")
