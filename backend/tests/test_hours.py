"""
Tests for daily/monthly hours aggregation.
Run from the backend folder:  python -m unittest discover tests
"""
import os
import sys
import unittest
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.hours import ShiftRecord, aggregate_month
from app.models import Attendance, User


def rec(uid, name, d, cin, cout, hours=None):
    def at(t):
        if t is None:
            return None
        if isinstance(t, datetime):
            return t
        h, m = map(int, t.split(":"))
        return datetime(d.year, d.month, d.day, h, m)
    return ShiftRecord(uid, name, d, at(cin), at(cout), hours)


NOV9 = date(2026, 11, 9)
NOV10 = date(2026, 11, 10)


class DailyAggregationTests(unittest.TestCase):
    def test_daily_total_is_sum_of_employees(self):
        out = aggregate_month([
            rec(1, "Naveen", NOV9, "09:00", "14:00"),
            rec(2, "Anil",   NOV9, "08:00", "18:00"),
        ], 2026, 11)
        day = out["days"][0]
        self.assertEqual(day["date"], "2026-11-09")
        self.assertEqual(day["total_minutes"], 15 * 60)
        self.assertEqual(day["total_hours"], 15)
        self.assertEqual(day["employee_count"], 2)
        by_name = {e["name"]: e["hours"] for e in day["employees"]}
        self.assertEqual(by_name, {"Naveen": 5, "Anil": 10})

    def test_minute_precision_and_two_decimal_display(self):
        out = aggregate_month([rec(1, "A", NOV9, "09:00", "16:20")], 2026, 11)
        day = out["days"][0]
        self.assertEqual(day["total_minutes"], 440)
        self.assertEqual(day["total_hours"], 7.33)

    def test_seconds_are_truncated(self):
        cin = datetime(2026, 11, 9, 9, 0, 59)
        cout = datetime(2026, 11, 9, 10, 0, 30)
        out = aggregate_month([rec(1, "A", NOV9, cin, cout)], 2026, 11)
        self.assertEqual(out["days"][0]["total_minutes"], 60)

    def test_no_records_means_no_days(self):
        out = aggregate_month([], 2026, 11)
        self.assertEqual(out["days"], [])
        self.assertEqual(out["summary"], {
            "total_minutes": 0, "total_hours": 0, "total_employees": 0, "working_days": 0,
        })

    def test_open_shift_counts_zero_and_is_flagged(self):
        out = aggregate_month([rec(1, "A", NOV9, "09:00", None)], 2026, 11)
        day = out["days"][0]
        self.assertEqual(day["total_minutes"], 0)
        self.assertEqual(day["in_progress_count"], 1)
        self.assertEqual(day["employee_count"], 0)
        self.assertTrue(day["employees"][0]["in_progress"])
        self.assertEqual(out["summary"]["working_days"], 0)

    def test_invalid_record_is_ignored(self):
        out = aggregate_month([rec(1, "A", NOV9, "17:00", "09:00")], 2026, 11)
        self.assertEqual(out["days"], [])

    def test_records_outside_month_are_ignored(self):
        out = aggregate_month([rec(1, "A", date(2026, 10, 31), "09:00", "17:00")], 2026, 11)
        self.assertEqual(out["days"], [])


class MultipleShiftTests(unittest.TestCase):
    def test_split_shifts_same_day_are_added(self):
        out = aggregate_month([
            rec(1, "A", NOV9, "08:00", "12:00"),
            rec(1, "A", NOV9, "13:00", "17:30"),
        ], 2026, 11)
        emp = out["days"][0]["employees"][0]
        self.assertEqual(emp["minutes"], 8 * 60 + 30)
        self.assertEqual(emp["shifts"], 2)
        self.assertEqual(out["days"][0]["employee_count"], 1)

    def test_duplicate_records_are_not_double_counted(self):
        out = aggregate_month([
            rec(1, "A", NOV9, "09:00", "17:00"),
            rec(1, "A", NOV9, "09:00", "17:00"),
        ], 2026, 11)
        self.assertEqual(out["days"][0]["total_minutes"], 8 * 60)

    def test_overlapping_records_are_merged(self):
        out = aggregate_month([
            rec(1, "A", NOV9, "09:00", "13:00"),
            rec(1, "A", NOV9, "12:00", "15:00"),
            rec(1, "A", NOV9, "10:00", "11:00"),   # fully contained
        ], 2026, 11)
        self.assertEqual(out["days"][0]["total_minutes"], 6 * 60)

    def test_same_times_for_different_employees_both_count(self):
        out = aggregate_month([
            rec(1, "A", NOV9, "09:00", "17:00"),
            rec(2, "B", NOV9, "09:00", "17:00"),
        ], 2026, 11)
        self.assertEqual(out["days"][0]["total_minutes"], 16 * 60)


class OvernightShiftTests(unittest.TestCase):
    def test_overnight_shift_counts_on_start_date(self):
        cin = datetime(2026, 11, 9, 22, 0)
        cout = datetime(2026, 11, 10, 6, 30)
        out = aggregate_month([rec(1, "A", NOV9, cin, cout)], 2026, 11)
        self.assertEqual(len(out["days"]), 1)
        self.assertEqual(out["days"][0]["date"], "2026-11-09")
        self.assertEqual(out["days"][0]["total_minutes"], 8 * 60 + 30)

    def test_overnight_then_next_day_shift_not_merged_across_dates(self):
        out = aggregate_month([
            rec(1, "A", NOV9, datetime(2026, 11, 9, 22, 0), datetime(2026, 11, 10, 2, 0)),
            rec(1, "A", NOV10, "09:00", "12:00"),
        ], 2026, 11)
        self.assertEqual([d["total_minutes"] for d in out["days"]], [240, 180])

    def test_month_end_overnight_shift_stays_in_start_month(self):
        d = date(2026, 11, 30)
        overnight = rec(1, "A", d, datetime(2026, 11, 30, 20, 0), datetime(2026, 12, 1, 4, 0))
        nov = aggregate_month([overnight], 2026, 11)
        dec = aggregate_month([overnight], 2026, 12)
        self.assertEqual(nov["summary"]["total_minutes"], 8 * 60)
        self.assertEqual(dec["summary"]["total_minutes"], 0)


class MonthlyTotalsTests(unittest.TestCase):
    def setUp(self):
        self.out = aggregate_month([
            rec(1, "Naveen", NOV9, "09:00", "14:00"),
            rec(2, "Anil",   NOV9, "08:00", "18:00"),
            rec(1, "Naveen", NOV10, "09:00", "09:07"),
            rec(3, "Sara",   date(2026, 11, 11), "10:00", None),  # still working
            rec(4, "Ravi",   date(2026, 11, 12), "08:00", "08:01"),
        ], 2026, 11)

    def test_monthly_total_equals_sum_of_daily_totals(self):
        s = self.out["summary"]
        self.assertEqual(s["total_minutes"], sum(d["total_minutes"] for d in self.out["days"]))
        self.assertEqual(s["total_minutes"], 15 * 60 + 7 + 1)

    def test_unique_employees_and_working_days(self):
        s = self.out["summary"]
        self.assertEqual(s["total_employees"], 3)   # Sara has no completed hours yet
        self.assertEqual(s["working_days"], 3)


class CalendarEndpointTests(unittest.TestCase):
    """Runs the endpoint against an in-memory database built from the real models."""

    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()
        naveen = User(full_name="Naveen", role="Cook", pin_hash="h1")
        anil = User(full_name="Anil", role="Cashier", pin_hash="h2", is_active=False)
        self.db.add_all([naveen, anil])
        self.db.flush()
        self.db.add_all([
            Attendance(user_id=naveen.id, date=NOV9, clock_in=datetime(2026, 11, 9, 9), clock_out=datetime(2026, 11, 9, 14)),
            Attendance(user_id=anil.id, date=NOV9, clock_in=datetime(2026, 11, 9, 8), clock_out=datetime(2026, 11, 9, 18)),
            Attendance(user_id=anil.id, date=date(2026, 12, 1), clock_in=datetime(2026, 12, 1, 8), clock_out=datetime(2026, 12, 1, 9)),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_endpoint_returns_daily_breakdown(self):
        from app.routers.manager import hours_calendar
        out = hours_calendar(2026, 11, self.db)
        self.assertEqual(len(out["days"]), 1)
        self.assertEqual(out["days"][0]["total_hours"], 15)
        self.assertEqual(out["summary"]["total_employees"], 2)
        self.assertIn("today", out)

    def test_endpoint_rejects_bad_month(self):
        from fastapi import HTTPException
        from app.routers.manager import hours_calendar
        with self.assertRaises(HTTPException):
            hours_calendar(2026, 13, self.db)


if __name__ == "__main__":
    unittest.main()
