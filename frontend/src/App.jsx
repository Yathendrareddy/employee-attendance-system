import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { Toast } from './components/Toast'

import PinLogin        from './pages/PinLogin'
import Register        from './pages/Register'
import EmployeeHome    from './pages/EmployeeHome'
import EmployeeReport  from './pages/EmployeeReport'
import ManagerDashboard from './pages/ManagerDashboard'

function ProtectedEmployee({ children }) {
  const { user } = useAuth()
  if (!user || user.is_manager) return <Navigate to="/" replace />
  return children
}

function ProtectedManager({ children }) {
  const { user } = useAuth()
  if (!user?.is_manager) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/"         element={<PinLogin />} />
          <Route path="/register" element={<Register />} />
          <Route path="/home"     element={<ProtectedEmployee><EmployeeHome /></ProtectedEmployee>} />
          <Route path="/report"   element={<ProtectedEmployee><EmployeeReport /></ProtectedEmployee>} />
          <Route path="/manager"  element={<ProtectedManager><ManagerDashboard /></ProtectedManager>} />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toast />
    </AuthProvider>
  )
}
