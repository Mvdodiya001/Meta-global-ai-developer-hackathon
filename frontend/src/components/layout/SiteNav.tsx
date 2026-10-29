import { NavLink } from 'react-router-dom'

const links = [
  { to: '/review', label: 'Clause review' },
  { to: '/impact', label: 'Source change' },
  { to: '/control', label: 'Lawyer control' },
] as const

export function SiteNav() {
  return (
    <nav
      aria-label="Primary"
      className="flex flex-wrap gap-2 border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-950"
    >
      <span className="mr-4 self-center text-sm font-semibold tracking-tight">
        ClauseTrace
      </span>
      {links.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            [
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              isActive
                ? 'bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-100'
                : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-900',
            ].join(' ')
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
