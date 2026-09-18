import { createContext, useCallback, useContext, useState } from 'react'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { cn } from './cn'

type ToastTone = 'success' | 'error' | 'info'

interface ToastItem {
  id: number
  tone: ToastTone
  title: string
  description?: string
}

interface ToastContextValue {
  show: (title: string, opts?: { tone?: ToastTone; description?: string }) => void
  success: (title: string, description?: string) => void
  error: (title: string, description?: string) => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

let counter = 0

const toneStyles: Record<ToastTone, { icon: React.ReactNode; ring: string }> = {
  success: { icon: <CheckCircle2 className="h-5 w-5 text-accent-600" />, ring: 'border-accent-200' },
  error: { icon: <AlertCircle className="h-5 w-5 text-rose-600" />, ring: 'border-rose-200' },
  info: { icon: <Info className="h-5 w-5 text-brand-600" />, ring: 'border-brand-200' },
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])

  const dismiss = useCallback((id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id))
  }, [])

  const show = useCallback<ToastContextValue['show']>((title, opts) => {
    const id = ++counter
    setItems((prev) => [...prev, { id, title, tone: opts?.tone || 'info', description: opts?.description }])
    window.setTimeout(() => dismiss(id), 4500)
  }, [dismiss])

  const value: ToastContextValue = {
    show,
    success: (title, description) => show(title, { tone: 'success', description }),
    error: (title, description) => show(title, { tone: 'error', description }),
  }

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-20 z-[100] flex flex-col items-center gap-2 px-4 sm:bottom-6">
        {items.map((item) => (
          <div
            key={item.id}
            role="status"
            className={cn(
              'pointer-events-auto flex w-full max-w-sm animate-slide-up items-start gap-3 rounded-2xl border bg-white p-4 shadow-card',
              toneStyles[item.tone].ring,
            )}
          >
            {toneStyles[item.tone].icon}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-ink-900">{item.title}</p>
              {item.description && <p className="mt-0.5 text-sm text-ink-500">{item.description}</p>}
            </div>
            <button
              type="button"
              onClick={() => dismiss(item.id)}
              className="text-ink-400 hover:text-ink-600"
              aria-label="Закрыть уведомление"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components -- hook lives with its provider by design
export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
