import { HTMLAttributes, forwardRef } from 'react'
import { cn } from './cn'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

const paddingClasses = {
  none: '',
  sm: 'p-4',
  md: 'p-5 sm:p-6',
  lg: 'p-6 sm:p-8',
}

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { className, interactive, padding = 'md', ...props },
  ref,
) {
  return (
    <div
      ref={ref}
      className={cn(
        'rounded-2xl border border-ink-100 bg-white shadow-soft',
        interactive && 'transition-all duration-150 hover:shadow-card hover:border-ink-200',
        paddingClasses[padding],
        className,
      )}
      {...props}
    />
  )
})

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mb-4 flex items-start justify-between gap-3', className)} {...props} />
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn('text-lg font-semibold text-ink-900 tracking-tight', className)} {...props} />
}
