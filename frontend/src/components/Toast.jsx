import { useState, useCallback } from 'react'

let _show = null

export function Toast() {
  const [toasts, setToasts] = useState([])

  _show = useCallback((msg, type = 'info') => {
    const id = Date.now()
    setToasts(t => [...t, { id, msg, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 2800)
  }, [])

  const icons = { success: 'ti-circle-check', error: 'ti-alert-circle', info: 'ti-info-circle' }
  const colors = { success: '#0E9F6E', error: '#E02424', info: '#1A56DB' }

  return (
    <div className="toast-wrap" style={{ display:'flex', flexDirection:'column', gap:'8px', alignItems:'center' }}>
      {toasts.map(t => (
        <div key={t.id} className="toast">
          <i className={`ti ${icons[t.type]}`} style={{ color: colors[t.type], fontSize: 18 }} />
          {t.msg}
        </div>
      ))}
    </div>
  )
}

export const toast = {
  success: (m) => _show?.(m, 'success'),
  error:   (m) => _show?.(m, 'error'),
  info:    (m) => _show?.(m, 'info'),
}
