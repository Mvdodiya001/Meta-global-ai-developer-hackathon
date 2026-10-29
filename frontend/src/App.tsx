import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from './components/layout/AppLayout'
import { ClauseReviewPage } from './pages/ClauseReviewPage'
import { LawyerControlPage } from './pages/LawyerControlPage'
import { SourceImpactPage } from './pages/SourceImpactPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/review" replace />} />
        <Route path="review" element={<ClauseReviewPage />} />
        <Route path="impact" element={<SourceImpactPage />} />
        <Route path="control" element={<LawyerControlPage />} />
      </Route>
    </Routes>
  )
}
