# 🏢 Employee Attendance System

A full-stack clock-in / clock-out system built with **React + FastAPI + SQLite**.

---

## 📁 Project Structure

```
EmployeeAttendanceSystem/
├── backend/
│   ├── app/
│   │   ├── main.py          ← FastAPI entry point + auto-clockout scheduler
│   │   ├── database.py      ← SQLite connection
│   │   ├── models.py        ← User + Attendance tables
│   │   ├── schemas.py       ← Pydantic request/response models
│   │   ├── auth.py          ← PIN hashing (bcrypt) + manager auth
│   │   └── routers/
│   │       ├── users.py     ← Register + Login
│   │       ├── attendance.py← Clock In / Out / Monthly Report
│   │       └── manager.py   ← Dashboard, All Reports, CSV Export
│   ├── seed.py              ← Add demo employees + sample data
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── PinLogin.jsx        ← PIN keypad login screen
    │   │   ├── Register.jsx        ← New employee registration
    │   │   ├── EmployeeHome.jsx    ← Clock In / Out + live status
    │   │   ├── EmployeeReport.jsx  ← Personal monthly report
    │   │   └── ManagerDashboard.jsx← Manager live view + all reports + CSV
    │   ├── components/
    │   │   ├── Toast.jsx      ← Notification toasts
    │   │   └── LiveClock.jsx  ← Real-time clock
    │   ├── context/
    │   │   └── AuthContext.jsx
    │   ├── services/
    │   │   └── api.js         ← All API calls (axios)
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## 🚀 Setup (VS Code)

### Step 1 — Open the project
```
Open VS Code → File → Open Folder → select EmployeeAttendanceSystem
```

---

### Step 2 — Backend setup

Open a **new terminal** in VS Code (`Ctrl + `` ` ``):

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed demo data (optional but recommended)
python seed.py

# Start the backend
uvicorn app.main:app --reload
```

Backend runs at: **http://localhost:8000**
API docs at:     **http://localhost:8000/docs**

---

### Step 3 — Frontend setup

Open a **second terminal** in VS Code:

```bash
cd frontend

# Install dependencies
npm install

# Start the frontend
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## 🔑 Demo Logins

| Name         | PIN  | Role       |
|--------------|------|------------|
| Sara Ahmed   | 1111 | Barista    |
| Ravi Kumar   | 2222 | Chef       |
| Nadia Hassan | 3333 | Cashier    |
| Tom Clarke   | 4444 | Supervisor |
| **Anil (Manager)** | **6472** | Manager |

---

## ⏰ Auto Clock-Out Rules

| Day            | Closing Time |
|----------------|-------------|
| Mon – Thu      | 10:00 PM    |
| Fri – Sat      | 11:00 PM    |
| Sunday         | 9:30 PM     |

The scheduler checks every minute. If an employee forgets to clock out, the system automatically closes their shift at store closing time.

---

## ✨ Features

- ✅ 4-digit PIN login (bcrypt hashed — never stored as plain text)
- ✅ Employee registration with role + phone
- ✅ Clock In / Clock Out with live status
- ✅ Prevents double clock-in or double clock-out
- ✅ Auto clock-out at closing time
- ✅ Employee personal monthly report (days worked, total hours, avg/day)
- ✅ Manager dashboard — live status of all employees
- ✅ Manager monthly report — per-employee breakdown
- ✅ CSV export (download attendance spreadsheet)
- ✅ Print support
- ✅ Toast notifications
- ✅ Fully responsive

---

## 🛠 Tech Stack

| Layer    | Technology              |
|----------|------------------------|
| Frontend | React 18, Vite, Axios  |
| Backend  | FastAPI, SQLAlchemy    |
| Database | SQLite                 |
| Auth     | bcrypt (passlib)       |
| Scheduler| APScheduler            |

---

## 📝 Notes

- The database file `attendance.db` is created automatically in the `backend/` folder on first run.
- To reset all data: delete `attendance.db` and run `python seed.py` again.
- To use PostgreSQL instead of SQLite: change `SQLALCHEMY_DATABASE_URL` in `database.py`.
