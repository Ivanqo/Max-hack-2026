import { cn } from './cn'

interface ProgressBarProps {
  value: number
  max?: number
  tone?: 'brand' | 'success' | 'warning' | 'danger'
  size?: 'sm' | 'md'
  className?: string
  label?: string
}

const toneClasses = {
  brand: 'bg-brand-600',
  success: 'bg-accent-500',
  warning: 'bg-amber-500',
  danger: 'bg-rose-500',
}

export function ProgressBar({ value, max = 100, tone = 'brand', size = 'md', className, label }: ProgressBarProps) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  return (
    <div
      className={cn('w-full overflow-hidden rounded-full bg-ink-100', size === 'sm' ? 'h-1.5' : 'h-2.5', className)}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-label={label}
    >
      <div
        className={cn('h-full rounded-full transition-all duration-500 ease-out', toneClasses[tone])}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
