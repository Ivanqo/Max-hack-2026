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

export function ReadinessRing({ value, size = 96 }: { value: number; size?: number }) {
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.max(0, Math.min(100, value)) / 100) * circumference
  const tone = value >= 70 ? '#0cc796' : value >= 40 ? '#f59e0b' : '#f43f5e'
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#ececf2" strokeWidth={10} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={tone}
          strokeWidth={10}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset .6s cubic-bezier(0.16,1,0.3,1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-ink-900">{Math.round(value)}%</span>
      </div>
    </div>
  )
}
