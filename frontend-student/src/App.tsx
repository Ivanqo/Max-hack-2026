import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuthStore } from './stores/authStore'
import { maxRoleDestination } from './lib/maxLaunch'
import { ToastProvider } from './ui'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import Home from './pages/Home'
import Onboarding from './pages/Onboarding'
import Knowledge from './pages/Knowledge'
import KnowledgeDetail from './pages/KnowledgeDetail'
import CareerGPS from './pages/CareerGPS'
import Opportunities from './pages/Opportunities'
import OpportunityDetail from './pages/OpportunityDetail'
import ProfilePage from './pages/ProfilePage'
import AboutPage from './pages/AboutPage'

declare global {
  interface Window {
    MAX?: { WebApp?: MaxWebApp }
    WebApp?: MaxWebApp
    Telegram?: { WebApp?: MaxWebApp }
    __MAX_DIAGNOSTICS__?: {
      bridgeAvailable: boolean
      initDataAvailable: boolean
      launchState: string
    }
  }
}

type MaxWebApp = { initData?: string; ready?: () => void }
type WebAppBridge = MaxWebApp | undefined
type LaunchState = 'loading' | 'error' | 'idle'

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

let bridgeLoadPromise: Promise<void> | null = null

function reloadMaxBridgeSdk(): Promise<void> {
  if (currentWebApp()) return Promise.resolve()
  if (bridgeLoadPromise) return bridgeLoadPromise

  bridgeLoadPromise = new Promise((resolve, reject) => {
    document.getElementById('max-bridge-sdk')?.remove()
    const script = document.createElement('script')
    script.id = 'max-bridge-sdk'
    script.src = 'https://st.max.ru/js/max-web-app.js'
    script.async = true
    let timeout = 0
    const finish = (error?: Error) => {
      window.clearTimeout(timeout)
      bridgeLoadPromise = null
      if (error || !currentWebApp()) reject(error || new Error('bridge unavailable'))
      else resolve()
    }
    timeout = window.setTimeout(() => finish(new Error('timeout')), 8000)
    script.onload = () => finish()
    script.onerror = () => finish(new Error('load failed'))
    document.head.appendChild(script)
  })
  return bridgeLoadPromise
}

function publishLaunchDiagnostics(bridgeAvailable: boolean, initDataAvailable: boolean, launchState: string) {
  const diagnostics = { bridgeAvailable, initDataAvailable, launchState }
  window.__MAX_DIAGNOSTICS__ = diagnostics
  // These booleans make startup diagnosable without exposing initData or identity.
  console.info('[MAX launch diagnostic]', diagnostics)
}

function launchErrorMessage(error: any): string {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (error?.response?.status === 409) {
    return 'Эта учётная запись уже связана с другим профилем MAX. Выйдите и войдите в нужную учётную запись.'
  }
  return 'Не удалось запустить UniPath MAX. Проверьте соединение и попробуйте ещё раз.'
}

function MaxLaunchBridge() {
  const navigate = useNavigate()
  const completeMaxLaunch = useAuthStore((state) => state.completeMaxLaunch)
  const [state, setState] = useState<LaunchState>('loading')
  const [message, setMessage] = useState('Подключаем UniPath MAX…')
  const [diagnostics, setDiagnostics] = useState({ bridgeAvailable: Boolean(currentWebApp()), initDataAvailable: false })
  const running = useRef(false)

  const launch = useCallback(async (retry = false) => {
    if (running.current) return
    running.current = true
    setState('loading')
    setMessage(retry ? 'Повторяем запуск…' : 'Подключаем UniPath MAX…')
    try {
      if (!currentWebApp()) await reloadMaxBridgeSdk()
      const webApp = currentWebApp()
      const initData = readLaunchInitData(webApp)
      const currentDiagnostics = { bridgeAvailable: Boolean(webApp), initDataAvailable: Boolean(initData) }
      setDiagnostics(currentDiagnostics)
      publishLaunchDiagnostics(currentDiagnostics.bridgeAvailable, currentDiagnostics.initDataAvailable, 'checking')
      if (!initData) {
        webApp?.ready?.()
        setMessage(webApp
          ? 'MAX не передал подписанные данные запуска. Закройте Mini App и откройте его снова из MAX.'
          : 'Не удалось загрузить MAX Bridge. Проверьте интернет-соединение и повторите попытку.')
        setState('error')
        publishLaunchDiagnostics(currentDiagnostics.bridgeAvailable, false, 'error')
        return
      }

      const { startParam, role } = await completeMaxLaunch(initData)
      sessionStorage.removeItem('max-launch-pending')
      webApp?.ready?.()
      publishLaunchDiagnostics(true, true, 'authenticated')
      const destination = maxRoleDestination(role)
      if (!destination) throw new Error('Unsupported account role')
      if (destination === '/admin/') {
        window.location.replace('/admin/')
        return
      }
      const match = /^opportunity_(\d+)$/.exec(startParam || '')
      if (match) navigate(`/opportunities?opportunity=${match[1]}`, { replace: true })
      setState('idle')
    } catch (error: any) {
      currentWebApp()?.ready?.()
      const currentDiagnostics = {
        bridgeAvailable: Boolean(currentWebApp()),
        initDataAvailable: Boolean(readLaunchInitData(currentWebApp())),
      }
      setDiagnostics(currentDiagnostics)
      publishLaunchDiagnostics(currentDiagnostics.bridgeAvailable, currentDiagnostics.initDataAvailable, 'error')
      if (error?.response?.data?.code === 'account_link_required') {
        const initData = readLaunchInitData(currentWebApp())
        if (initData) {
          sessionStorage.setItem('max-launch-pending', initData)
          setState('idle')
          navigate('/login', { replace: true })
          return
        }
      }
      setMessage(launchErrorMessage(error))
      setState('error')
    } finally {
      running.current = false
    }
  }, [completeMaxLaunch, navigate])

  useEffect(() => {
    void launch()
  }, [launch])

  if (state === 'idle') return null
  return (
    <div className="fixed inset-x-3 top-3 z-[100] mx-auto max-w-lg rounded-2xl border border-ink-200 bg-white p-4 shadow-card" role={state === 'error' ? 'alert' : 'status'}>
      <p className="text-sm font-semibold text-ink-900">{state === 'loading' ? 'Запуск Mini App' : 'MAX Mini App не запущено'}</p>
      <p className="mt-1 text-sm text-ink-600">{message}</p>
      <p className="mt-2 text-xs text-ink-400">
        Диагностика: Bridge {diagnostics.bridgeAvailable ? 'доступен' : 'не найден'} · подписанные данные {diagnostics.initDataAvailable ? 'получены' : 'не получены'}
      </p>
      {state === 'error' && (
        <button
          className="mt-3 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          onClick={() => void launch(true)}
          type="button"
        >
          Повторить запуск
        </button>
      )}
    </div>
  )
}

function App() {
  return (
    <div className="theme-student min-h-screen">
      <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <MaxLaunchBridge />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/onboarding" element={<Onboarding />} />
              <Route element={<Layout />}>
                <Route path="/" element={<Navigate to="/home" replace />} />
                <Route path="/dashboard" element={<Navigate to="/home" replace />} />
                <Route path="/home" element={<Home />} />
                <Route path="/knowledge" element={<Knowledge />} />
                <Route path="/knowledge/:id" element={<KnowledgeDetail />} />
                <Route path="/career-gps" element={<CareerGPS />} />
                <Route path="/opportunities" element={<Opportunities />} />
                <Route path="/opportunities/:id" element={<OpportunityDetail />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/about" element={<AboutPage />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </ToastProvider>
      </BrowserRouter>
    </div>
  )
}

export default App
