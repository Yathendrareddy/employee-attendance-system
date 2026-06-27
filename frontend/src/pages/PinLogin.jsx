import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { loginPin } from '../services/api'
import LiveClock from '../components/LiveClock'
import { toast } from '../components/Toast'

export default function PinLogin() {
  const [pin, setPin]       = useState('')
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate  = useNavigate()

  const press = (d) => {
    if (pin.length >= 4) return
    const next = pin + d
    setPin(next)
    setError('')
    if (next.length === 4) setTimeout(() => submit(next), 180)
  }

  const clear = () => setPin(p => p.slice(0, -1))

  const submit = async (p = pin) => {
    if (p.length !== 4) return
    setLoading(true)
    try {
      const { data } = await loginPin(p)
      login(data)
      toast.success(`Welcome, ${data.name}!`)
      navigate(data.is_manager ? '/manager' : '/home')
    } catch (e) {
      const msg = e.response?.data?.detail || 'Invalid PIN'
      setError(msg)
      setPin('')
    } finally {
      setLoading(false)
    }
  }

  const keys = ['1','2','3','4','5','6','7','8','9']

  return (
    <div className="app-shell">
      <div className="card pin-screen">
        <div className="company-logo">
          <i className="ti ti-building-store" style={{ fontSize: 28, color: '#1A56DB' }} />
        </div>
        <div className="screen-title">Staff Clock-In</div>
        <div className="screen-sub">Enter your 4-digit PIN to continue</div>

        <LiveClock />

        <div className="pin-dots">
          {[0,1,2,3].map(i => (
            <div key={i} className={`pin-dot ${i < pin.length ? 'filled' : ''}`} />
          ))}
        </div>

        <div className="pin-grid">
          {keys.map(k => (
            <button key={k} className="pin-key" onClick={() => press(k)} disabled={loading}>{k}</button>
          ))}
          <button className="pin-key action" onClick={clear} disabled={loading}>
            <i className="ti ti-backspace" style={{ fontSize: 20 }} />
          </button>
          <button className="pin-key" onClick={() => press('0')} disabled={loading}>0</button>
          <button className="pin-key submit" onClick={() => submit()} disabled={loading || pin.length < 4}>
            {loading ? <span className="spinner" /> : <i className="ti ti-arrow-right" style={{ fontSize: 20 }} />}
          </button>
        </div>

        <div className="pin-error">
          {error && <><i className="ti ti-alert-circle" /> {error}</>}
        </div>

        <div className="register-link">
          New employee?{' '}
          <button onClick={() => navigate('/register')}>Register here</button>
        </div>
      </div>
    </div>
  )
}
