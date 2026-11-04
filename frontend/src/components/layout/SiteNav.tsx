import { NavLink } from 'react-router-dom'

import {
  IconClause,
  IconControl,
  IconGraph,
  IconImpact,
  IconMatters,
  IconMic,
  IconReview,
  IconSignIn,
} from '../ui/Icons'

type NavItem = {
  to: string
  label: string
  icon: typeof IconMatters
  end?: boolean
}

const GROUPS: { label: string; links: NavItem[] }[] = [
  {
    label: 'Workspace',
    links: [
      { to: '/', label: 'Your matters', icon: IconMatters, end: true },
      { to: '/review', label: 'Review a clause', icon: IconReview },
      { to: '/impact', label: 'Law changes', icon: IconImpact },
      { to: '/compare', label: 'Compare documents', icon: IconGraph },
      { to: '/control', label: 'Your control room', icon: IconControl },
    ],
  },
  {
    label: 'Drafting',
    links: [
      { to: '/clauses', label: 'Update clauses', icon: IconClause },
      { to: '/dictate', label: 'Dictate a fact', icon: IconMic },
    ],
  },
  {
    label: 'Account',
    links: [{ to: '/signin', label: 'Sign in', icon: IconSignIn }],
  },
]

/**
 * One navigation, two shapes: a persistent sidebar on desktop and a
 * single-row, horizontally scrollable rail on narrow screens.
 * `/admin` is intentionally absent — it is a staff surface only.
 */
export function SiteNav() {
  return (
    <nav aria-label="Primary" className="ct-nav">
      {GROUPS.map((group) => (
        <div key={group.label} className="contents lg:block">
          <p className="ct-nav-group">{group.label}</p>
          {group.links.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className="ct-nav-link">
              <Icon size={17} />
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  )
}
