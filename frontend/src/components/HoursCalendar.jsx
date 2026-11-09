import { useState, useEffect, useCallback, useRef } from 'react'
import { hoursCalendar } from '../services/api'

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const POLL_MS = 60_000

const pad = (n) => String(n).padStart(2, '0')
const isoDate = (y, m, d) => `${y}-${pad(m)}-${pad(d)}`
// Up to two decimals, no trailing zeros: 15 -> "15", 7.5 -> "7.5", 7.33 -> "7.33"
const fmtHrs = (h) => `${Number((h ?? 0).toFixed(2))} hrs`
const longDate = (iso) => {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
}

export default function HoursCalendar({ refreshToken }) {
  const [view, setView] = useState(() => {
    const n = new Date()
    return { year: n.getFullYear(), month: n.getMonth() + 1 }
  })
  const [data,     setData]     = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)
  const [selected, setSelected] = useState(null)   // 'YYYY-MM-DD' – stays highlighted
  const [modalOpen, setModalOpen] = useState(false)
  const reqId = useRef(0)

  const load = useCallback(async (silent) => {
    const id = ++reqId.current
    if (!silent) { setLoading(true); setError(null) }
    try {
      const { data: res } = await hoursCalendar(view.year, view.month)
      if (id !== reqId.current) return              // a newer request superseded this one
      setData(res)
      setError(null)
    } catch (e) {
      if (id !== reqId.current) return
      // On a background refresh keep showing the last good data; only surface the error.
      setError(e.response?.data?.detail || 'Could not load attendance hours.')
      if (!silent) setData(null)
    } finally {
      if (id === reqId.current && !silent) setLoading(false)
    }
  }, [view])

  // Month change → full load
  useEffect(() => { load(false) }, [load])

  // Parent signals a data change (manual entry, clock-out-all, edits) → silent refresh
  useEffect(() => { if (refreshToken) load(true) }, [refreshToken])   // eslint-disable-line react-hooks/exhaustive-deps

  // Pick up clock-ins/outs made on other devices without a page reload
  useEffect(() => {
    const tick = () => { if (!document.hidden) load(true) }
    const timer = setInterval(tick, POLL_MS)
    window.addEventListener('focus', tick)
    return () => { clearInterval(timer); window.removeEventListener('focus', tick) }
  }, [load])

  useEffect(() => {
    if (!modalOpen) return
    const onKey = (e) => { if (e.key === 'Escape') setModalOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [modalOpen])

  const shiftMonth = (delta) => {
    setModalOpen(false)
    setSelected(null)
    setView(({ year, month }) => {
      const d = new Date(year, month - 1 + delta, 1)
      return { year: d.getFullYear(), month: d.getMonth() + 1 }
    })
  }

  const { year, month } = view
  const monthTitle = new Date(year, month - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  const firstWeekday = new Date(year, month - 1, 1).getDay()
  const daysInMonth = new Date(year, month, 0).getDate()
  const cells = [
    ...Array(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]
  while (cells.length % 7) cells.push(null)

  const byDate = Object.fromEntries((data?.days ?? []).map(d => [d.date, d]))
  const selectedDay = selected ? (byDate[selected] ?? null) : null

  const openDay = (iso) => { setSelected(iso); setModalOpen(true) }

  return (
    <div className="hours-cal">
      <div className="cal-toolbar">
        <button className="btn btn-ghost btn-sm" onClick={() => shiftMonth(-1)} aria-label="Previous month">
          <i className="ti ti-chevron-left" />
        </button>
        <div className="cal-title">{monthTitle}</div>
        <button className="btn btn-ghost btn-sm" onClick={() => shiftMonth(1)} aria-label="Next month">
          <i className="ti ti-chevron-right" />
        </button>
      </div>

      {error && data && (
        <div className="cal-warning"><i className="ti ti-alert-triangle" /> {error} Showing the last loaded data.</div>
      )}

      {loading ? (
        <div className="loading"><div className="spinner" style={{ borderColor: 'rgba(0,0,0,.1)', borderTopColor: '#1A56DB' }} /> Loading...</div>
      ) : !data ? (
        <div className="empty-state">
          <i className="ti ti-cloud-off" />
          Attendance data is unavailable.<br />
          <span className="text-muted">{error}</span>
          <div className="mt-2">
            <button className="btn btn-ghost btn-sm" style={{ margin: '0 auto' }} onClick={() => load(false)}>
              <i className="ti ti-refresh" /> Retry
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="cal-grid">
            {WEEKDAYS.map((w, i) => (
              <div key={w} className={`cal-weekday ${i === 0 ? 'is-sun' : ''} ${i === 6 ? 'is-sat' : ''}`}>{w}</div>
            ))}
            {cells.map((day, idx) => {
              if (day === null) return <div key={`blank-${idx}`} className="cal-day cal-blank" />
              const iso = isoDate(year, month, day)
              const info = byDate[iso]
              const hrs = info?.total_hours ?? 0
              const weekday = idx % 7
              const cls = [
                'cal-day',
                weekday === 0 && 'is-sun',
                weekday === 6 && 'is-sat',
                iso === data.today && 'is-today',
                iso === selected && 'is-selected',
                hrs > 0 && 'has-hours',
              ].filter(Boolean).join(' ')
              return (
                <button key={iso} className={cls} onClick={() => openDay(iso)}
                        aria-label={`${longDate(iso)}: ${fmtHrs(hrs)}`}>
                  <span className="cal-date">{day}</span>
                  <span className="cal-hrs"><span className="cal-hrs-label">Total Hrs : </span>{fmtHrs(hrs)}</span>
                  {info?.in_progress_count > 0 && (
                    <span className="cal-live" title={`${info.in_progress_count} still clocked in`}>
                      <i className="ti ti-circle-filled" /> {info.in_progress_count} working
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          <div className="dash-grid cal-summary">
            <div className="dash-card blue">
              <div className="dash-icon"><i className="ti ti-clock-hour-4" /></div>
              <div className="dash-num">{fmtHrs(data.summary.total_hours)}</div>
              <div className="dash-lbl">Monthly Total Hours</div>
            </div>
            <div className="dash-card green">
              <div className="dash-icon"><i className="ti ti-users" /></div>
              <div className="dash-num">{data.summary.total_employees}</div>
              <div className="dash-lbl">Total Employees</div>
            </div>
            <div className="dash-card orange">
              <div className="dash-icon"><i className="ti ti-calendar-check" /></div>
              <div className="dash-num">{data.summary.working_days}</div>
              <div className="dash-lbl">Total Working Days</div>
            </div>
          </div>
        </>
      )}

      {modalOpen && selected && (
        <DayHoursModal iso={selected} day={selectedDay} onClose={() => setModalOpen(false)} />
      )}
    </div>
  )
}

function DayHoursModal({ iso, day, onClose }) {
  const employees = day?.employees ?? []
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="card modal-box" role="dialog" aria-modal="true" aria-labelledby="day-hours-title"
           onClick={e => e.stopPropagation()}>
        <div className="mgr-header" style={{ marginBottom: '1rem' }}>
          <div>
            <div className="screen-title" id="day-hours-title" style={{ fontSize: 18 }}>
              <i className="ti ti-calendar-event" style={{ marginRight: 8, color: '#1A56DB' }} />
              Employee Hours
            </div>
            <div className="screen-sub">{longDate(iso)}</div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Close"><i className="ti ti-x" /></button>
        </div>

        {employees.length === 0 ? (
          <div className="empty-state" style={{ padding: '2rem' }}>
            <i className="ti ti-clock-off" />No hours recorded for this date.
          </div>
        ) : (
          <table className="cal-table">
            <thead>
              <tr><th>Employee</th><th>Working Hours</th></tr>
            </thead>
            <tbody>
              {employees.map(e => (
                <tr key={e.id}>
                  <td>
                    {e.name}
                    {e.shifts > 1 && <span className="text-muted"> · {e.shifts} shifts</span>}
                  </td>
                  <td>
                    {fmtHrs(e.hours)}
                    {e.in_progress && <span className="badge-clocked-in" style={{ marginLeft: 8 }}>In progress</span>}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="tfoot-row"><td>Total Employees</td><td>{day.employee_count}</td></tr>
              <tr className="tfoot-row"><td>Total Hrs</td><td>{fmtHrs(day.total_hours)}</td></tr>
            </tfoot>
          </table>
        )}

        <button className="btn btn-primary mt-2" style={{ width: '100%' }} onClick={onClose}>Close</button>
      </div>
    </div>
  )
}
