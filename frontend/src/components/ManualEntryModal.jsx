import { useState, useMemo } from 'react'
import { useAuth } from '../context/AuthContext'
import { manualAttendance } from '../services/api'
import { toast } from '../components/Toast'

const todayStr = () => new Date().toISOString().slice(0, 10)

export default function ManualEntryModal({ employees, onClose, onSaved }) {
  const { user } = useAuth()
  const [search,   setSearch]   = useState('')
  const [selected, setSelected] = useState(() => new Set())
  const [date,     setDate]     = useState(todayStr())
  const [clockIn,  setClockIn]  = useState('')
  const [clockOut, setClockOut] = useState('')
  const [saving,   setSaving]   = useState(false)

  const filtered = useMemo(
    () => employees.filter(e => e.name.toLowerCase().includes(search.toLowerCase())),
    [employees, search]
  )

  const toggle = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const selectAllFiltered = () => setSelected(new Set(filtered.map(e => e.id)))
  const clearSelection    = () => setSelected(new Set())

  const handleSave = async () => {
    if (selected.size === 0) { toast.error('Select at least one employee.'); return }
    if (!clockIn && !clockOut) { toast.error('Enter a clock in or clock out time.'); return }

    setSaving(true)
    try {
      await manualAttendance({
        employee_ids: [...selected],
        date,
        clock_in: clockIn || null,
        clock_out: clockOut || null,
        manager_id: user?.id ?? null,
      })
      toast.success(`Timesheet updated for ${selected.size} employee${selected.size > 1 ? 's' : ''}.`)
      onSaved()
      onClose()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to update timesheet.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="card modal-box" onClick={e => e.stopPropagation()}>
        <div className="mgr-header" style={{ marginBottom: '1rem' }}>
          <div className="screen-title" style={{ fontSize: 18 }}>
            <i className="ti ti-calendar-plus" style={{ marginRight: 8, color: '#1A56DB' }} />
            Manual Time Entry
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><i className="ti ti-x" /></button>
        </div>

        <div className="form-group">
          <label>Employees</label>
          <input
            className="form-control"
            placeholder="Search employees by name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 2px', fontSize: 12 }}>
            <span className="text-muted">{selected.size} selected</span>
            <span style={{ display: 'flex', gap: 10 }}>
              <button className="back-btn" style={{ margin: 0 }} onClick={selectAllFiltered}>Select all</button>
              <button className="back-btn" style={{ margin: 0 }} onClick={clearSelection}>Clear</button>
            </span>
          </div>
          <div className="emp-picker">
            {filtered.length === 0 && <div className="empty-state" style={{ padding: '1.5rem' }}>No employees found</div>}
            {filtered.map(e => (
              <label className="emp-picker-row" key={e.id}>
                <input type="checkbox" checked={selected.has(e.id)} onChange={() => toggle(e.id)} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{e.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-2)' }}>{e.role}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Date</label>
          <input type="date" className="form-control" value={date} onChange={e => setDate(e.target.value)} />
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Clock In</label>
            <input type="time" className="form-control" value={clockIn} onChange={e => setClockIn(e.target.value)} />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Clock Out</label>
            <input type="time" className="form-control" value={clockOut} onChange={e => setClockOut(e.target.value)} />
          </div>
        </div>

        <div className="text-muted mb-1">
          Leave a time blank to only set the other. Existing entries for the selected date will be updated;
          employees without one will get a new entry.
        </div>

        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <span className="spinner" style={{ width: 16, height: 16 }} /> : <i className="ti ti-device-floppy" />}
          {saving ? 'Saving...' : 'Save Timesheet'}
        </button>
        <button className="btn btn-ghost" onClick={onClose} disabled={saving}>Cancel</button>
      </div>
    </div>
  )
}
