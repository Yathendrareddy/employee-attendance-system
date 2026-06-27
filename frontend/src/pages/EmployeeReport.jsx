import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { monthlyReport } from '../services/api'
import { toast } from '../components/Toast'

export default function EmployeeReport() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const now = new Date()
  const [year,  setYear]  = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [data,  setData]  = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { if (!user || user.is_manager) { navigate('/'); return } fetch() }, [year, month])

  const fetch = async () => {
    setLoading(true)
    try {
      const { data: d } = await monthlyReport(user.id, year, month)
      setData(d)
    } catch { toast.error('Failed to load report.') }
    finally { setLoading(false) }
  }

  const monthOptions = Array.from({ length: 12 }, (_, i) => ({
    val: i + 1,
    label: new Date(2000, i, 1).toLocaleDateString('en-US', { month: 'long' })
  }))

  const fmt    = (dt) => dt ? new Date(dt).toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit' }) : '—'
  const fmtDate = (d) => new Date(d.replace(/-/g, '/')).toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' })

  const avgHours = data?.days_worked
    ? (data.total_hours / data.days_worked).toFixed(2)
    : '0.00'

  const printReport = () => window.print()

  return (
    <div className="app-shell">
      <div className="card report-screen">
        <button className="back-btn" onClick={() => navigate('/home')}>
          <i className="ti ti-arrow-left" /> Back
        </button>

        <div className="report-header">
          <div>
            <div className="screen-title">{user?.name?.split(' ')[0]}'s Report</div>
            <div className="screen-sub">Monthly attendance summary</div>
          </div>
          <div style={{ display:'flex', gap:8, alignItems:'center', flexWrap:'wrap' }}>
            <select className="select-ctrl" value={month} onChange={e => setMonth(+e.target.value)}>
              {monthOptions.map(m => <option key={m.val} value={m.val}>{m.label}</option>)}
            </select>
            <select className="select-ctrl" value={year} onChange={e => setYear(+e.target.value)}>
              {[now.getFullYear(), now.getFullYear()-1].map(y =>
                <option key={y} value={y}>{y}</option>
              )}
            </select>
            <button className="btn btn-ghost btn-sm" onClick={printReport}>
              <i className="ti ti-printer" /> Print
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-num">{data?.days_worked ?? '—'}</div>
            <div className="stat-lbl">Days Worked</div>
          </div>
          <div className="stat-card">
            <div className="stat-num">{data?.total_hours ?? '—'}</div>
            <div className="stat-lbl">Total Hours</div>
          </div>
          <div className="stat-card">
            <div className="stat-num">{avgHours}</div>
            <div className="stat-lbl">Avg Hours/Day</div>
          </div>
        </div>

        {loading ? (
          <div className="loading"><div className="spinner" style={{borderColor:'rgba(0,0,0,.1)',borderTopColor:'#1A56DB'}}/> Loading...</div>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Clock In</th>
                  <th>Clock Out</th>
                  <th>Hours</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {data?.records?.length === 0 && (
                  <tr><td colSpan={5} className="empty-state">No records this month</td></tr>
                )}
                {data?.records?.map((r, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight:500 }}>{fmtDate(r.date)}</td>
                    <td>{fmt(r.clock_in)}</td>
                    <td>
                      {fmt(r.clock_out)}
                      {r.auto_clocked_out && <span className="auto-badge">auto</span>}
                    </td>
                    <td style={{ fontWeight:600, color: r.hours_worked ? '#1A56DB' : undefined }}>
                      {r.hours_worked ?? '—'}
                    </td>
                    <td style={{ color:'#9CA3AF', fontSize:12 }}>
                      {r.auto_clocked_out ? 'Auto closed at store closing' : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
              {data?.total_hours > 0 && (
                <tfoot>
                  <tr className="tfoot-row">
                    <td colSpan={3} style={{ padding:'11px 14px' }}>Total</td>
                    <td style={{ padding:'11px 14px' }}>{data.total_hours} hrs</td>
                    <td />
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
