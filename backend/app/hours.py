"""
Daily / monthly employee-hours aggregation used by the manager calendar.

Policies (kept in one place so the calendar, its popup and the monthly summary agree):

* Business timezone: all timestamps are naive store-local times (see app.tz.STORE_TZ).
* Shift date: a shift belongs to the Attendance.date it was opened on. A shift that
  crosses midnight is counted entirely on its start date, never split or double-counted.
* Precision: every shift is measured in whole minutes (seconds are truncated on both
  ends). Totals are summed in minutes and only converted to hours for display, so the
  monthly total is exactly the sum of the daily totals.
* Overlaps / duplicates: an employee's shifts on the same date are merged as time
  intervals before summing, so duplicate or overlapping records count once.
* Missing data: open shifts (clocked in, not yet out) count 0 minutes and are flagged
  as in progress. Records with clock_out <= clock_in are ignored. Nothing is invented.
* Unpaid breaks: the schema does not record breaks, so no deduction is applied.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Optional


@dataclass
class ShiftRecord:
    user_id: int
    name: str
    date: date
    clock_in: Optional[datetime]
    clock_out: Optional[datetime]
    hours_worked: Optional[float] = None


def _to_minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def minutes_to_hours(minutes: int) -> float:
    return round(minutes / 60, 2)


def _merged_minutes(intervals):
    """Total minutes covered by a list of (start, end) intervals, counting overlaps once."""
    total = 0
    cur_start = cur_end = None
    for start, end in sorted(intervals):
        if cur_end is None or start > cur_end:
            if cur_end is not None:
                total += int((cur_end - cur_start) / timedelta(minutes=1))
            cur_start, cur_end = start, end
        elif end > cur_end:
            cur_end = end
    if cur_end is not None:
        total += int((cur_end - cur_start) / timedelta(minutes=1))
    return total


def aggregate_month(records: Iterable[ShiftRecord], year: int, month: int) -> dict:
    """Group attendance records by date and employee and compute minute-precise totals."""
    # (date, user_id) -> working state
    buckets = defaultdict(lambda: {"intervals": [], "extra_minutes": 0, "shifts": 0, "in_progress": False})
    names = {}

    for r in records:
        if r.date.year != year or r.date.month != month:
            continue
        names[r.user_id] = r.name
        b = buckets[(r.date, r.user_id)]

        if r.clock_in and r.clock_out:
            start, end = _to_minute(r.clock_in), _to_minute(r.clock_out)
            if end > start:
                b["intervals"].append((start, end))
                b["shifts"] += 1
        elif r.clock_in and not r.clock_out:
            b["in_progress"] = True
        elif r.hours_worked:
            # Legacy record with a stored duration but no timestamps.
            b["extra_minutes"] += round(r.hours_worked * 60)
            b["shifts"] += 1

    days = defaultdict(list)
    for (d, uid), b in buckets.items():
        minutes = _merged_minutes(b["intervals"]) + b["extra_minutes"]
        if minutes == 0 and not b["in_progress"]:
            continue
        days[d].append({
            "id": uid,
            "name": names[uid],
            "minutes": minutes,
            "hours": minutes_to_hours(minutes),
            "shifts": b["shifts"],
            "in_progress": b["in_progress"],
        })

    day_list = []
    month_minutes = 0
    worked_ids = set()
    for d in sorted(days):
        emps = sorted(days[d], key=lambda e: (-e["minutes"], e["name"].lower()))
        day_minutes = sum(e["minutes"] for e in emps)
        month_minutes += day_minutes
        worked_ids.update(e["id"] for e in emps if e["minutes"] > 0)
        day_list.append({
            "date": d.isoformat(),
            "total_minutes": day_minutes,
            "total_hours": minutes_to_hours(day_minutes),
            "employee_count": sum(1 for e in emps if e["minutes"] > 0),
            "in_progress_count": sum(1 for e in emps if e["in_progress"]),
            "employees": emps,
        })

    return {
        "year": year,
        "month": month,
        "days": day_list,
        "summary": {
            "total_minutes": month_minutes,
            "total_hours": minutes_to_hours(month_minutes),
            "total_employees": len(worked_ids),
            "working_days": sum(1 for d in day_list if d["total_minutes"] > 0),
        },
    }
