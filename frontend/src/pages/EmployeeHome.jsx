import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { clockIn, clockOut, todayStatus } from '../services/api'
import { toast } from '../components/Toast'
import LiveClock from '../components/LiveClock'

const AVATAR_COLORS = [
  { bg:'#DBEAFE', color:'#1E40AF' },
  { bg:'#D1FAE5', color:'#065F46' },
  { bg:'#FCE7F3', color:'#9D174D' },
  { bg:'#FEF3C7', color:'#92400E' },
  { bg:'#EDE9FE', color:'#5B21B6' },
]

export default function EmployeeHome() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [status, setStatus]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)

  const av = AVATAR_COLORS[(user?.id || 0) % AVATAR_COLORS.length]
  const initials = (user?.name || 'U').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase()

  useEffect(() => {
    if (!user || user.is_manager) { navigate('/'); return }
    fetchStatus()
  }, [])

  const fetchStatus = async () => {
    try {
      const { data } = await todayStatus(user.id)
      setStatus(data)
    } catch { toast.error('Could not load status.') }
    finally { setFetching(false) }
  }

  const handleClockIn = async () => {
    setLoading(true)
    try {
      await clockIn(user.id)
      toast.success('Clocked in successfully!')
      fetchStatus()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Clock-in failed.')
    } finally { setLoading(false) }
  }

  const handleClockOut = async () => {
    setLoading(true)
    try {
      const { data } = await clockOut(user.id)
      toast.success(`Clocked out! ${data.hours_worked} hrs today.`)
      fetchStatus()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Clock-out failed.')
    } finally { setLoading(false) }
  }

  const handleLogout = () => { logout(); navigate('/') }

  const fmt = (dt) => dt ? new Date(dt).toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit' }) : '—'

  return (
    <div className="app-shell">
      <div className="card home-screen">
        <div style={{ textAlign:'center' }}>
          <div className="avatar" style={{ background: av.bg, color: av.color }}>{initials}</div>
          <div className="emp-name">{user?.name}</div>
          <div className="emp-role">{user?.role}</div>

          {fetching ? (
            <div className="loading"><div className="spinner" style={{ borderColor:'rgba(0,0,0,.15)', borderTopColor: '#1A56DB' }} /> Loading...</div>
          ) : (
            <>
              {/* Status badge */}
              {status?.status === 'clocked_in' && (
                <span className="status-badge badge-in">
                  <i className="ti ti-circle-filled" style={{ fontSize:8 }} /> Currently Working
                </span>
              )}
              {status?.status === 'clocked_out' && (
                <span className="status-badge badge-done">
                  <i className="ti ti-moon" style={{ fontSize:14 }} /> Shift Complete
                </span>
              )}
              {status?.status === 'not_clocked_in' && (
                <span className="status-badge badge-out">
                  <i className="ti ti-circle-x" style={{ fontSize:14 }} /> Not Clocked In
                </span>
              )}

              <LiveClock />

              {/* Info row */}
              <div className="info-row">
                <div className="info-item">
                  <div className="info-label">Clock In</div>
                  <div className="info-val">{fmt(status?.clock_in)}</div>
                </div>
                <div className="info-item">
                  <div className="info-label">Clock Out</div>
                  <div className="info-val">{fmt(status?.clock_out)}</div>
                </div>
                <div className="info-item">
                  <div className="info-label">Hours</div>
                  <div className="info-val">{status?.hours_worked ?? '—'}</div>
                </div>
              </div>

              {/* Actions */}
              {status?.status === 'not_clocked_in' && (
                <button className="btn btn-success" onClick={handleClockIn} disabled={loading}>
                  {loading ? <span className="spinner"/> : <i className="ti ti-login"/>}
                  Clock In
                </button>
              )}
              {status?.status === 'clocked_in' && (
                <button className="btn btn-danger" onClick={handleClockOut} disabled={loading}>
                  {loading ? <span className="spinner"/> : <i className="ti ti-logout"/>}
                  Clock Out
                </button>
              )}
              {status?.status === 'clocked_out' && (
                <div style={{ padding:'10px', background:'#F0FDF4', borderRadius:10, marginBottom:4, fontSize:14, color:'#065F46', fontWeight:500 }}>
                  <i className="ti ti-check" /> Great work today! See you next shift.
                </div>
              )}
            </>
          )}

          <div className="divider" />
          <button className="btn btn-ghost" onClick={() => navigate('/report')}>
            <i className="ti ti-calendar-stats" /> My Monthly Report
          </button>
          <button className="btn btn-ghost" onClick={handleLogout} style={{ marginTop: 8 }}>
            <i className="ti ti-logout" /> Sign Out
          </button>
        </div>
      </div>
    </div>
  )
}
