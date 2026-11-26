import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from app.database import Base, engine, SessionLocal
from app.routers import users, attendance, manager
from app import models
from app.tz import store_now
from app.closing import auto_close_open_shifts

def auto_clockout_job():
    db = SessionLocal()
    try:
        auto_close_open_shifts(db, store_now())
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    try:
        auto_clockout_job()   # catch up on shifts left open while the server was down
    except Exception:
        logging.exception("Startup auto clock-out sweep failed; the scheduler will retry")
    scheduler.add_job(auto_clockout_job, "interval", minutes=1)
    scheduler.start()
    yield
    scheduler.shutdown()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Employee Attendance System", lifespan=lifespan)

default_origins = "http://localhost:5173,http://localhost:3000"
allowed_origins = [o.strip().rstrip("/") for o in os.getenv("ALLOWED_ORIGINS", default_origins).split(",") if o.strip()]

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
