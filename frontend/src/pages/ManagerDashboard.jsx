import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { managerDashboard, allEmployees, managerReport, exportCSV, exportExcel, deleteEmployee, editAttendance, clockOutAll } from '../services/api'
import { toast } from '../components/Toast'
import ManualEntryModal from '../components/ManualEntryModal'

const AVATAR_COLORS = [
  { bg:'#DBEAFE', color:'#1E40AF' },
  { bg:'#D1FAE5', color:'#065F46' },
  { bg:'#FCE7F3', color:'#9D174D' },
  { bg:'#FEF3C7', color:'#92400E' },
  { bg:'#EDE9FE', color:'#5B21B6' },
  { bg:'#FEE2E2', color:'#991B1B' },
]

const initials = (name='') => name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()
const fmt      = (dt) => dt ? new Date(dt).toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'}) : '—'
const fmtDate  = (d)  => new Date(d.replace(/-/g, '/')).toLocaleDateString('en-US',{month:'short',day:'numeric'})

export default function ManagerDashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const now = new Date()

  const [tab,    setTab]    = useState('live')
  const [dash,   setDash]   = useState(null)
  const [emps,   setEmps]   = useState([])
  const [report, setReport] = useState([])
  const [year,   setYear]   = useState(now.getFullYear())
  const [month,  setMonth]  = useState(now.getMonth()+1)
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editIn,  setEditIn]  = useState('')
  const [editOut, setEditOut] = useState('')
  const [showManual, setShowManual] = useState(false)

  useEffect(() => {
    if (!user?.is_manager) { navigate('/'); return }
    loadDash()
    loadEmps()
  }, [])

  useEffect(() => { if (tab === 'report') loadReport() }, [tab, year, month])

  const loadDash  = async () => { try { const {data} = await managerDashboard(); setDash(data) } catch {} }
  const loadEmps  = async () => { try { const {data} = await allEmployees();     setEmps(data) } catch { toast.error('Failed to load employees.') } }
  const loadReport = async () => {
    setLoading(true)
    try { const {data} = await managerReport(year, month); setReport(data) }
    catch { toast.error('Failed to load report.') }
    finally { setLoading(false) }
  }

  const handleExport = () => { window.open(exportCSV(year, month), '_blank') }
  const handleExportExcel = () => { window.open(exportExcel(year, month), '_blank') }
  const handleLogout = () => { logout(); navigate('/') }

  const handlePrint = () => {
    if (loading) { toast.error('Report is still loading, please wait.'); return }
    if (report.length === 0) { toast.error('No report data to print.'); return }
    window.print()
  }

  const handleClockOutAll = async () => {
    if (!window.confirm('Clock out every employee currently clocked in? This cannot be undone.')) return
    try {
      const { data } = await clockOutAll(user?.id ?? null)
      toast.success(data.clocked_out > 0 ? `Clocked out ${data.clocked_out} employee${data.clocked_out === 1 ? '' : 's'}.` : 'No one was clocked in.')
      loadEmps()
      loadDash()
      if (tab === 'report') loadReport()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to clock out employees.')
    }
  }

  const handleDeleteEmployee = async (emp) => {
    if (!window.confirm(`Remove ${emp.name}? Their attendance history will be kept, but they won't be able to clock in anymore.`)) return
    try {
      await deleteEmployee(emp.id)
      toast.success(`${emp.name} removed.`)
      loadEmps()
      loadDash()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to remove employee.')
    }
  }

  const toTimeInput = (dt) => {
    if (!dt) return ''
    const d = new Date(dt)
    return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
  }

  const startEdit = (r) => {
    setEditingId(r.id)
    setEditIn(toTimeInput(r.clock_in))
    setEditOut(toTimeInput(r.clock_out))
  }

  const cancelEdit = () => { setEditingId(null); setEditIn(''); setEditOut('') }

  const saveEdit = async () => {
    try {
      await editAttendance(editingId, { clock_in: editIn || null, clock_out: editOut || null })
      toast.success('Hours updated.')
      cancelEdit()
      loadReport()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to update hours.')
    }
  }

  const monthOptions = Array.from({length:12},(_,i)=>({
    val:i+1, label:new Date(2000,i,1).toLocaleDateString('en-US',{month:'long'})
  }))
  const monthLabel = monthOptions.find(m => m.val === month)?.label ?? ''

  const recordStatus = (r) => {
    if (!r.clock_in) return '—'
    if (!r.clock_out) return 'In Progress'
    return r.auto_clocked_out ? 'Auto Clock-Out' : 'Present'
  }

  const StatusBadge = ({ s }) => {
    if (s === 'clocked_in')  return <span className="badge-clocked-in"><i className="ti ti-circle-filled" style={{fontSize:8}}/>Working</span>
    if (s === 'clocked_out') return <span className="badge-clocked-out"><i className="ti ti-check"/>Done</span>
    return <span className="badge-not-in"><i className="ti ti-minus"/>Not In</span>
  }

  return (
    <>
    <div className="app-shell no-print" style={{alignItems:'flex-start',paddingTop:'2rem'}}>
      <div className="card mgr-screen">

        {/* Header */}
        <div className="mgr-header">
          <div>
            <div className="screen-title">
              <i className="ti ti-layout-dashboard" style={{marginRight:8,color:'#1A56DB'}}/> Manager Dashboard
            </div>
            <div className="screen-sub">Welcome, Anil &nbsp;·&nbsp; {now.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'})}</div>
          </div>
          <div style={{display:'flex',gap:10,flexWrap:'wrap'}}>
            <button className="btn btn-primary btn-sm" onClick={()=>setShowManual(true)}>
              <i className="ti ti-calendar-plus"/> Manual Time Entry
            </button>
            <button className="btn btn-danger btn-sm" onClick={handleClockOutAll}>
              <i className="ti ti-logout-2"/> All Clock Out
            </button>
            <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
              <i className="ti ti-logout"/> Sign Out
            </button>
          </div>
        </div>

        {showManual && (
          <ManualEntryModal
            employees={emps}
            onClose={() => setShowManual(false)}
            onSaved={() => { loadEmps(); loadDash(); if (tab === 'report') loadReport() }}
          />
        )}

        {/* Dash cards */}
        {dash && (
          <div className="dash-grid">
            <div className="dash-card blue">
              <div className="dash-icon"><i className="ti ti-users"/></div>
              <div className="dash-num">{dash.total_employees}</div>
              <div className="dash-lbl">Total Employees</div>
            </div>
            <div className="dash-card green">
              <div className="dash-icon"><i className="ti ti-user-check"/></div>
              <div className="dash-num">{dash.working_now}</div>
              <div className="dash-lbl">Working Now</div>
            </div>
            <div className="dash-card orange">
              <div className="dash-icon"><i className="ti ti-clock-hour-4"/></div>
              <div className="dash-num">{dash.today_hours}</div>
              <div className="dash-lbl">Today's Hours</div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="section-tabs">
          <button className={`tab-btn ${tab==='live'?'active':''}`}    onClick={()=>setTab('live')}>
            <i className="ti ti-activity"/> Live Status
          </button>
          <button className={`tab-btn ${tab==='report'?'active':''}`}  onClick={()=>setTab('report')}>
            <i className="ti ti-calendar-stats"/> Monthly Report
          </button>
        </div>

        {/* ── Live Tab ── */}
        {tab === 'live' && (
          <div>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr><th>Employee</th><th>Role</th><th>Status</th><th>Clock In</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  {emps.length === 0 && (
                    <tr><td colSpan={5}>
                      <div className="empty-state"><i className="ti ti-users"/>No employees registered yet</div>
                    </td></tr>
                  )}
                  {emps.map((e,i)=>(
                    <tr key={e.id}>
                      <td>
                        <div style={{display:'flex',alignItems:'center',gap:10}}>
                          <div className="mini-avatar" style={{background:AVATAR_COLORS[i%AVATAR_COLORS.length].bg,color:AVATAR_COLORS[i%AVATAR_COLORS.length].color}}>
                            {initials(e.name)}
                          </div>
                          <div>
                            <div style={{fontWeight:600}}>{e.name}</div>
                            {e.phone && <div style={{fontSize:12,color:'#9CA3AF'}}>{e.phone}</div>}
                          </div>
                        </div>
                      </td>
                      <td style={{color:'#6B7280'}}>{e.role}</td>
                      <td><StatusBadge s={e.today_status}/></td>
                      <td>{fmt(e.clock_in)}</td>
                      <td>
                        <button className="btn btn-ghost btn-sm" style={{color:'#E02424'}} onClick={()=>handleDeleteEmployee(e)}>
                          <i className="ti ti-trash"/> Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Report Tab ── */}
        {tab === 'report' && (
          <div>
            {/* Controls */}
            <div style={{display:'flex',gap:10,marginBottom:'1.2rem',flexWrap:'wrap',alignItems:'center'}}>
              <select className="select-ctrl" value={month} onChange={e=>setMonth(+e.target.value)}>
                {monthOptions.map(m=><option key={m.val} value={m.val}>{m.label}</option>)}
              </select>
              <select className="select-ctrl" value={year} onChange={e=>setYear(+e.target.value)}>
                {[now.getFullYear(),now.getFullYear()-1].map(y=><option key={y} value={y}>{y}</option>)}
              </select>
              <button className="btn btn-ghost btn-sm" onClick={handleExport}>
                <i className="ti ti-download"/> Export CSV
              </button>
              <button className="btn btn-ghost btn-sm" onClick={handleExportExcel}>
                <i className="ti ti-file-spreadsheet"/> Export Excel
              </button>
              <button className="btn btn-ghost btn-sm" onClick={handlePrint}>
                <i className="ti ti-printer"/> Print
              </button>
            </div>

            {loading ? (
              <div className="loading"><div className="spinner" style={{borderColor:'rgba(0,0,0,.1)',borderTopColor:'#1A56DB'}}/> Loading...</div>
            ) : (
              report.map((emp, ei) => (
                <div className="emp-block" key={emp.id}>
                  <div className="emp-block-header">
                    <div className="mini-avatar" style={{background:AVATAR_COLORS[ei%AVATAR_COLORS.length].bg,color:AVATAR_COLORS[ei%AVATAR_COLORS.length].color,width:40,height:40,fontSize:14}}>
                      {initials(emp.name)}
                    </div>
                    <div>
                      <div style={{fontWeight:700,fontSize:15}}>{emp.name}</div>
                      <div style={{fontSize:12,color:'#6B7280'}}>
                        {emp.role} &nbsp;·&nbsp; {emp.days_worked} days &nbsp;·&nbsp; <strong style={{color:'#1A56DB'}}>{emp.total_hours} hrs</strong>
                      </div>
                    </div>
                  </div>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr><th>Date</th><th>Clock In</th><th>Clock Out</th><th>Hours</th><th>Actions</th></tr>
                      </thead>
                      <tbody>
                        {emp.records.length === 0 && (
                          <tr><td colSpan={5} className="empty-state">No records this month</td></tr>
                        )}
                        {emp.records.map((r,i) => (
                          <tr key={i}>
                            <td>{fmtDate(r.date)}</td>
                            {editingId === r.id ? (
                              <>
                                <td><input type="time" className="select-ctrl" value={editIn} onChange={e=>setEditIn(e.target.value)} /></td>
                                <td><input type="time" className="select-ctrl" value={editOut} onChange={e=>setEditOut(e.target.value)} /></td>
                                <td style={{fontWeight:600}}>{r.hours_worked ?? '—'}</td>
                                <td style={{display:'flex',gap:6}}>
                                  <button className="btn btn-ghost btn-sm" onClick={saveEdit}><i className="ti ti-check"/> Save</button>
                                  <button className="btn btn-ghost btn-sm" onClick={cancelEdit}><i className="ti ti-x"/> Cancel</button>
                                </td>
                              </>
                            ) : (
                              <>
                                <td>{fmt(r.clock_in)}</td>
                                <td>{fmt(r.clock_out)}{r.auto_clocked_out && <span className="auto-badge">auto</span>}</td>
                                <td style={{fontWeight:600,color:r.hours_worked?'#1A56DB':undefined}}>{r.hours_worked ?? '—'}</td>
                                <td>
                                  <button className="btn btn-ghost btn-sm" onClick={()=>startEdit(r)}><i className="ti ti-pencil"/> Edit</button>
                                </td>
                              </>
                            )}
                          </tr>
                        ))}
                      </tbody>
                      {emp.total_hours > 0 && (
                        <tfoot>
                          <tr className="tfoot-row">
                            <td colSpan={3} style={{padding:'10px 14px'}}>Total</td>
                            <td colSpan={2} style={{padding:'10px 14px'}}>{emp.total_hours} hrs</td>
                          </tr>
                        </tfoot>
                      )}
                    </table>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>

    {/* Print-only timesheets: one printable page per employee. Rendered as a sibling
        of the (display:none-in-print) dashboard so it isn't hidden along with it. */}
    <div className="print-only">
      {report.map((emp) => (
        <section className="print-page" key={emp.id}>
          <h1 className="print-title">Employee Timesheet</h1>
          <table className="print-meta">
            <tbody>
              <tr><td>Employee Name</td><td>{emp.name}</td></tr>
              <tr><td>Role</td><td>{emp.role}</td></tr>
              <tr><td>Month / Year</td><td>{monthLabel} {year}</td></tr>
              <tr><td>Working Days</td><td>{emp.days_worked}</td></tr>
              <tr><td>Total Hours Worked</td><td>{emp.total_hours}</td></tr>
            </tbody>
          </table>

          <table className="print-table">
            <thead>
              <tr><th>Date</th><th>Clock In</th><th>Clock Out</th><th>Hours</th><th>Status</th></tr>
            </thead>
            <tbody>
              {emp.records.length === 0 && (
                <tr><td colSpan={5}>No records this month</td></tr>
              )}
              {emp.records.map((r, ri) => (
                <tr key={ri}>
                  <td>{fmtDate(r.date)}</td>
                  <td>{fmt(r.clock_in)}</td>
                  <td>{fmt(r.clock_out)}</td>
                  <td>{r.hours_worked ?? '—'}</td>
                  <td>{recordStatus(r)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="print-summary">
            <span>Total Working Days: <strong>{emp.days_worked}</strong></span>
            <span>Total Hours: <strong>{emp.total_hours}</strong></span>
          </div>

          <div className="print-signatures">
            <div className="sig-block"><span className="sig-line"/>Employee Signature</div>
            <div className="sig-block"><span className="sig-line"/>Manager Signature</div>
            <div className="sig-block"><span className="sig-line"/>Date</div>
          </div>
        </section>
      ))}
    </div>
    </>
  )
}
