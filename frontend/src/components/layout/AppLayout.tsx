import { Outlet } from 'react-router-dom'
import { DisclaimerBanner } from './DisclaimerBanner'
import { SiteNav } from './SiteNav'

export function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <DisclaimerBanner />
      <SiteNav />
      <div className="flex-1 px-4 py-6">
        <Outlet />
      </div>
    </div>
  )
}
