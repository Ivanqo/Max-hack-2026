import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import Home from './pages/Home'
import Onboarding from './pages/Onboarding'
import Knowledge from './pages/Knowledge'
import CareerGPS from './pages/CareerGPS'
import Opportunities from './pages/Opportunities'
import ProfilePage from './pages/ProfilePage'

declare global {
  interface Window {
    MAX?: { WebApp?: { initData?: string; ready?: () => void } }
    WebApp?: { initData?: string; ready?: () => void }
    Telegram?: { WebApp?: { initData?: string; ready?: () => void } }
  }
}

type WebAppBridge = { initData?: string; ready?: () => void } | undefined

function currentWebApp(): WebAppBridge {
  return window.MAX?.WebApp || window.WebApp || window.Telegram?.WebApp
}

function readLaunchInitData(webApp: WebAppBridge): string {
  if (webApp?.initData) {
    return webApp.initData
  }

  const candidates = [
    window.location.hash.replace(/^#/, ''),
    window.location.search.replace(/^\?/, ''),
  ]
  for (const candidate of candidates) {
    if (!candidate) continue
    const params = new URLSearchParams(candidate)
    if (
      params.has('WebAppData') ||
      params.has('web_app_data') ||
      params.has('initData') ||
      params.has('init_data') ||
      params.has('hash')
    ) {
      return candidate
    }
  }
  return ''
}

function MaxLaunchBridge() {
  const navigate = useNavigate()
  const completeMaxLaunch = useAuthStore((state) => state.completeMaxLaunch)

  useEffect(() => {
    const webApp = currentWebApp()
    const initData = readLaunchInitData(webApp)
    if (!initData || sessionStorage.getItem('max-launch-processed') === initData) {
      webApp?.ready?.()
      return
    }
    sessionStorage.setItem('max-launch-processed', initData)
    completeMaxLaunch(initData)
      .then((startParam) => {
        webApp?.ready?.()
        const match = /^opportunity_(\d+)$/.exec(startParam || '')
        if (match) {
          navigate(`/opportunities?opportunity=${match[1]}`, { replace: true })
        }
      })
      .catch(() => {
        webApp?.ready?.()
      })
  }, [completeMaxLaunch, navigate])

  return null
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <MaxLaunchBridge />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/home" replace />} />
              <Route path="/dashboard" element={<Navigate to="/home" replace />} />
              <Route path="/home" element={<Home />} />
              <Route path="/onboarding" element={<Onboarding />} />
              <Route path="/knowledge" element={<Knowledge />} />
              <Route path="/career-gps" element={<CareerGPS />} />
              <Route path="/opportunities" element={<Opportunities />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
