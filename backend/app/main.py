import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from datetime import datetime, date

from app.database import Base, engine, SessionLocal
from app.routers import users, attendance, manager
from app import models

def auto_clockout_job():
    db = SessionLocal()
    try:
        today = date.today()
        now = datetime.now()
        weekday = today.weekday()  # 0=Mon ... 6=Sun
        closing = {0:22,1:22,2:22,3:22,4:23,5:23,6:21}
        closing_min = {0:0,1:0,2:0,3:0,4:0,5:0,6:30}
        close_hour = closing[weekday]
        close_min  = closing_min[weekday]

        if now.hour == close_hour and now.minute == close_min:
            open_records = (
                db.query(models.Attendance)
                .filter(models.Attendance.date == today, models.Attendance.clock_out == None)
                .all()
            )
            for rec in open_records:
                rec.clock_out = now.replace(second=0, microsecond=0)
                rec.auto_clocked_out = True
            db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_clockout_job, "interval", minutes=1)
    scheduler.start()
    yield
    scheduler.shutdown()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Employee Attendance System", lifespan=lifespan)

default_origins = "http://localhost:5173,http://localhost:3000"
allowed_origins = os.getenv("ALLOWED_ORIGINS", default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(manager.router, prefix="/api/manager", tags=["Manager"])

@app.get("/")
def root():
    return {"message": "Employee Attendance System API Running ✓"}
