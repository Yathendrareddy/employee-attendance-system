import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { registerUser } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { toast } from '../components/Toast'

export default function Register() {
  const [form, setForm]     = useState({ full_name:'', role:'', pin:'', pin2:'', phone:'' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate  = useNavigate()

  const change = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const submit = async () => {
    setError('')
    if (!form.full_name.trim()) return setError('Full name is required.')
    if (!form.role.trim())      return setError('Role is required.')
    if (!/^\d{4}$/.test(form.pin)) return setError('PIN must be exactly 4 digits.')
    if (form.pin !== form.pin2) return setError("PINs don't match.")

    setLoading(true)
    try {
      const { data } = await registerUser({
        full_name: form.full_name,
        role:      form.role,
        pin:       form.pin,
        phone:     form.phone || null,
      })
      // Auto-login after register
      login({ id: data.id, name: data.name, role: form.role, is_manager: false })
      toast.success(`Account created! Welcome, ${data.name.split(' ')[0]}!`)
      navigate('/home')
    } catch (e) {
      setError(e.response?.data?.detail || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <div className="card form-screen">
        <button className="back-btn" onClick={() => navigate('/')}>
          <i className="ti ti-arrow-left" /> Back
        </button>
        <div className="screen-title">Create Account</div>
        <div className="screen-sub" style={{ marginBottom: '1.4rem' }}>
          Fill in your details to get started
        </div>

        <div className="form-group">
          <label>Full name</label>
          <input className="form-control" name="full_name" placeholder="e.g. Sara Ahmed"
            value={form.full_name} onChange={change} />
        </div>
        <div className="form-group">
          <label>Role / Position</label>
          <input className="form-control" name="role" placeholder="e.g. Barista"
            value={form.role} onChange={change} />
        </div>
        <div className="form-group">
          <label>Phone (optional)</label>
          <input className="form-control" name="phone" placeholder="e.g. 050 123 4567"
            value={form.phone} onChange={change} />
        </div>
        <div className="form-group">
          <label>Choose a 4-digit PIN</label>
          <input className="form-control" name="pin" type="password" inputMode="numeric"
            maxLength={4} placeholder="••••" value={form.pin} onChange={change} />
        </div>
        <div className="form-group">
          <label>Confirm PIN</label>
          <input className="form-control" name="pin2" type="password" inputMode="numeric"
            maxLength={4} placeholder="••••" value={form.pin2} onChange={change} />
        </div>

        {error && (
          <div className="pin-error" style={{ marginBottom: 10 }}>
            <i className="ti ti-alert-circle" /> {error}
          </div>
        )}

        <button className="btn btn-primary" onClick={submit} disabled={loading}>
          {loading ? <span className="spinner" /> : <i className="ti ti-user-plus" />}
          Create Account
        </button>
      </div>
    </div>
  )
}
