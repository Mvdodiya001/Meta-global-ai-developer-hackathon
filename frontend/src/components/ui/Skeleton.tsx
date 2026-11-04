type SkeletonProps = {
  lines?: number
  className?: string
  label?: string
}

/** Content-shaped loading placeholder that announces itself politely. */
export function Skeleton({ lines = 3, className = '', label = 'Loading' }: SkeletonProps) {
  return (
    <div
      className={`space-y-2.5 ${className}`}
      aria-busy="true"
      aria-label={label}
      role="progressbar"
    >
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="ct-skeleton h-3.5"
          style={{ width: `${Math.max(38, 96 - index * 16)}%` }}
        />
      ))}
    </div>
  )
}

export function PanelSkeleton({ label = 'Loading section' }: { label?: string }) {
  return (
    <div className="border-t border-ct-line pt-4" role="progressbar" aria-label={label} aria-busy="true">
      <div className="ct-skeleton mb-4 h-3 w-40" />
      <Skeleton lines={4} label={label} />
    </div>
  )
}
