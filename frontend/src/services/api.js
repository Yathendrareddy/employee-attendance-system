import axios from 'axios'

// In local dev, requests to '/api' go through the Vite proxy to localhost:8000.
// In production (deployed separately from the backend), VITE_API_URL points at the live backend.
const API_ROOT = import.meta.env.VITE_API_URL || ''
const api = axios.create({ baseURL: `${API_ROOT}/api` })

// Users
export const loginPin      = (pin)  => api.post('/users/login',    { pin })
export const registerUser  = (data) => api.post('/users/register', data)

// Attendance
export const clockIn       = (user_id) => api.post('/attendance/clock-in',  { user_id })
export const clockOut      = (user_id) => api.post('/attendance/clock-out', { user_id })
export const todayStatus   = (user_id) => api.get(`/attendance/today/${user_id}`)
export const monthlyReport = (user_id, year, month) =>
  api.get(`/attendance/monthly/${user_id}`, { params: { year, month } })

// Manager
export const managerDashboard  = ()            => api.get('/manager/dashboard')
export const allEmployees      = ()            => api.get('/manager/employees')
export const managerReport     = (year, month) => api.get('/manager/report',  { params: { year, month } })
export const exportCSV         = (year, month) =>
  `${API_ROOT}/api/manager/export-csv?year=${year}&month=${month}`
export const deleteEmployee    = (user_id)     => api.delete(`/manager/employees/${user_id}`)
export const editAttendance    = (record_id, data) => api.patch(`/manager/attendance/${record_id}`, data)
export const manualAttendance  = (data)        => api.post('/manager/attendance/manual', data)
export const clockOutAll       = (manager_id)  => api.post('/manager/attendance/clock-out-all', { manager_id })
