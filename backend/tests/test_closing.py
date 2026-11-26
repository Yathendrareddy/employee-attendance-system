"""
Tests for store closing times and automatic clock-out.
Run from the backend folder:  python -m unittest discover tests
"""
import os
import sys
import unittest
from datetime import date, datetime, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.closing import auto_close_open_shifts, closing_datetime
from app.database import Base
from app.models import Attendance, User

# Week of Nov 23-29, 2026: Mon 23 ... Sun 29
MON, THU, FRI, SAT, SUN = (date(2026, 11, d) for d in (23, 26, 27, 28, 29))


class ClosingTimeTests(unittest.TestCase):
    def test_schedule(self):
        self.assertEqual(closing_datetime(MON).time(), time(22, 0))
        self.assertEqual(closing_datetime(THU).time(), time(22, 0))
        self.assertEqual(closing_datetime(FRI).time(), time(23, 0))
        self.assertEqual(closing_datetime(SAT).time(), time(23, 0))
        self.assertEqual(closing_datetime(SUN).time(), time(21, 10))


class AutoCloseTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()
        self.user = User(full_name="A", role="Server", pin_hash="h")
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def add(self, d, cin, cout=None):
        rec = Attendance(user_id=self.user.id, date=d, clock_in=cin, clock_out=cout)
        self.db.add(rec)
        self.db.commit()
        return rec

    def test_not_closed_before_closing_time(self):
        rec = self.add(SUN, datetime(2026, 11, 29, 11, 0))
        self.assertEqual(auto_close_open_shifts(self.db, datetime(2026, 11, 29, 21, 9)), 0)
        self.assertIsNone(rec.clock_out)

    def test_closed_at_sunday_closing_with_hours(self):
        rec = self.add(SUN, datetime(2026, 11, 29, 11, 0))
        self.assertEqual(auto_close_open_shifts(self.db, datetime(2026, 11, 29, 21, 10)), 1)
        self.assertEqual(rec.clock_out, datetime(2026, 11, 29, 21, 10))
        self.assertEqual(rec.hours_worked, 10.17)
        self.assertTrue(rec.auto_clocked_out)

    def test_catch_up_uses_closing_time_not_run_time(self):
        """Server was asleep at closing; the sweep the next morning still closes at closing time."""
        rec = self.add(FRI, datetime(2026, 11, 27, 15, 0))
        auto_close_open_shifts(self.db, datetime(2026, 11, 28, 9, 30))
        self.assertEqual(rec.clock_out, datetime(2026, 11, 27, 23, 0))
        self.assertEqual(rec.hours_worked, 8.0)

    def test_completed_shifts_untouched(self):
        rec = self.add(MON, datetime(2026, 11, 23, 9, 0), datetime(2026, 11, 23, 17, 0))
        self.assertEqual(auto_close_open_shifts(self.db, datetime(2026, 11, 24, 9, 0)), 0)
        self.assertEqual(rec.clock_out, datetime(2026, 11, 23, 17, 0))
        self.assertFalse(rec.auto_clocked_out)

    def test_clock_in_after_closing_waits_for_end_of_day(self):
        rec = self.add(SUN, datetime(2026, 11, 29, 21, 30))
        self.assertEqual(auto_close_open_shifts(self.db, datetime(2026, 11, 29, 23, 0)), 0)
        self.assertIsNone(rec.clock_out)
        auto_close_open_shifts(self.db, datetime(2026, 11, 30, 0, 0))
        self.assertEqual(rec.clock_out, datetime(2026, 11, 29, 21, 30))
        self.assertEqual(rec.hours_worked, 0)
        self.assertTrue(rec.auto_clocked_out)


if __name__ == "__main__":
    unittest.main()
