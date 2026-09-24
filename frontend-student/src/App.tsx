import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuthStore } from './stores/authStore'
import {
  createMaxSdkLoader,
  launchMaxApp,
  MaxLaunchStartupError,
  MaxWebAppBridge,
  waitForMaxBridgeSdk,
} from './lib/maxLaunch'
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
    MAX?: { WebApp?: MaxWebAppBridge }
    WebApp?: MaxWebAppBridge
    Telegram?: { WebApp?: MaxWebAppBridge }
    __MAX_DIAGNOSTICS__?: {
      bridgeAvailable: boolean
      initDataAvailable: boolean
      launchState: string
    }
  }
}

type WebAppBridge = MaxWebAppBridge | undefined
type LaunchState = 'loading' | 'error' | 'idle'

function currentWebApp(): WebAppBridge {
  return window.MAX?.WebApp || window.WebApp || window.Telegram?.WebApp
}

const loadMaxBridgeSdk = createMaxSdkLoader(() =>
  waitForMaxBridgeSdk(currentWebApp, { timeoutMs: 15_000, pollIntervalMs: 100 }),
)

function publishLaunchDiagnostics(bridgeAvailable: boolean, initDataAvailable: boolean, launchState: string) {
  const diagnostics = { bridgeAvailable, initDataAvailable, launchState }
  window.__MAX_DIAGNOSTICS__ = diagnostics
  // These booleans make startup diagnosable without exposing initData or identity.
  console.info('[MAX launch diagnostic]', diagnostics)
}

function launchErrorMessage(error: any): string {
  if (error instanceof MaxLaunchStartupError) {
    return error.kind === 'sdk_timeout'
      ? 'MAX Bridge не загрузился. Проверьте соединение и повторите запуск.'
      : 'MAX не передал данные запуска. Закройте Mini App и откройте его снова из MAX.'
  }
  const detail = error?.response?.data?.detail
  if (error?.response?.status === 400 && detail === 'Invalid MAX launch context.') {
    return 'MAX не подтвердил данные запуска. Закройте Mini App и откройте его снова из MAX.'
  }
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
  const pendingInitData = useRef('')

  const launch = useCallback(async (retry = false) => {
    if (running.current) return
    running.current = true
    pendingInitData.current = ''
    // No success gate is persisted: a new MAX launch always reads fresh bridge state.
    sessionStorage.removeItem('max-launch-pending')
    setState('loading')
    setMessage(retry ? 'Повторяем запуск…' : 'Подключаем UniPath MAX…')
    try {
      const result = await launchMaxApp({
        getWebApp: currentWebApp,
        loadSdk: loadMaxBridgeSdk,
        completeLaunch: completeMaxLaunch,
        timeoutMs: 8_000,
        pollIntervalMs: 80,
        onStage: (stage) => {
          const webApp = currentWebApp()
          const currentDiagnostics = {
            bridgeAvailable: Boolean(webApp),
            initDataAvailable: Boolean(webApp?.initData?.trim()),
          }
          setDiagnostics(currentDiagnostics)
          publishLaunchDiagnostics(currentDiagnostics.bridgeAvailable, currentDiagnostics.initDataAvailable, stage)
          if (stage === 'waiting_for_context') webApp?.ready?.()
        },
        onContext: ({ initData }) => {
          pendingInitData.current = initData
          // Retain only in memory until account_link_required; never log the signed payload.
        },
      })
      sessionStorage.removeItem('max-launch-pending')
      if (result.destination === '/admin/') {
        window.location.replace('/admin/')
        return
      }
      const match = /^opportunity_(\d+)$/.exec(result.startParam || '')
      if (match) navigate(`/opportunities?opportunity=${match[1]}`, { replace: true })
      else navigate(result.destination, { replace: true })
      setState('idle')
    } catch (error: any) {
      const webApp = currentWebApp()
      const currentDiagnostics = { bridgeAvailable: Boolean(webApp), initDataAvailable: Boolean(webApp?.initData?.trim()) }
      setDiagnostics(currentDiagnostics)
      publishLaunchDiagnostics(currentDiagnostics.bridgeAvailable, currentDiagnostics.initDataAvailable, 'error')
      if (error?.response?.data?.code === 'account_link_required') {
        if (pendingInitData.current) {
          sessionStorage.setItem('max-launch-pending', pendingInitData.current)
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
          onClick={() => {
            if (!currentWebApp()) window.location.reload()
            else void launch(true)
          }}
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
