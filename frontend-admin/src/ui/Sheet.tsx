import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { cn } from './cn'

interface SheetProps {
  open: boolean
  onClose: () => void
  title?: string
  description?: string
  children: React.ReactNode
  className?: string
  side?: 'right' | 'center'
}

/** Slide-over drawer from the right on desktop, full-width bottom sheet on mobile. */
export function Sheet({ open, onClose, title, description, children, className, side = 'right' }: SheetProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-stretch sm:justify-end">
      <div
        className="absolute inset-0 animate-fade-in bg-ink-950/40 backdrop-blur-[2px]"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          'safe-bottom relative z-10 flex max-h-[90vh] w-full animate-slide-up flex-col overflow-y-auto rounded-t-3xl bg-white p-5 shadow-card',
          side === 'right'
            ? 'sm:h-full sm:max-h-none sm:w-full sm:max-w-lg sm:rounded-none sm:rounded-l-3xl sm:p-6'
            : 'sm:max-w-lg sm:animate-scale-in sm:rounded-3xl sm:p-6',
          className,
        )}
      >
        <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-ink-200 sm:hidden" />
        {title && (
          <div className="mb-1 flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-ink-900">{title}</h2>
              {description && <p className="mt-0.5 text-sm text-ink-500">{description}</p>}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-600"
              aria-label="Закрыть"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
        <div className="mt-4 flex-1">{children}</div>
      </div>
    </div>,
    document.body,
  )
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Удалить',
  danger = true,
  loading,
}: {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description?: string
  confirmLabel?: string
  danger?: boolean
  loading?: boolean
}) {
  if (!open) return null
  return createPortal(
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-ink-950/40" onClick={onClose} aria-hidden="true" />
      <div role="alertdialog" aria-modal="true" className="relative z-10 w-full max-w-sm animate-scale-in rounded-2xl bg-white p-6 shadow-card">
        <h2 className="text-base font-semibold text-ink-900">{title}</h2>
        {description && <p className="mt-2 text-sm text-ink-500">{description}</p>}
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-ink-200 px-4 py-2 text-sm font-medium text-ink-700 hover:bg-ink-50"
          >
            Отмена
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={cn(
              'rounded-xl px-4 py-2 text-sm font-medium text-white disabled:opacity-60',
              danger ? 'bg-rose-600 hover:bg-rose-700' : 'bg-brand-600 hover:bg-brand-700',
            )}
          >
            {loading ? 'Удаляем…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
