import { Route, Routes } from 'react-router-dom'

import { AppLayout } from './components/layout/AppLayout'
import { AdminPage } from './pages/AdminPage'
import { ClauseReviewPage } from './pages/ClauseReviewPage'
import { ClausesPage } from './pages/ClausesPage'
import { DictationPage } from './pages/DictationPage'
import { EvidencePage } from './pages/EvidencePage'
import { LawyerControlPage } from './pages/LawyerControlPage'
import { MattersPage } from './pages/MattersPage'
import { SignInPage } from './pages/SignInPage'
import { SourceImpactPage } from './pages/SourceImpactPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<MattersPage />} />
        <Route path="review" element={<ClauseReviewPage />} />
        <Route path="impact" element={<SourceImpactPage />} />
        <Route path="control" element={<LawyerControlPage />} />
        <Route path="evidence/:findingId" element={<EvidencePage />} />
        <Route path="dictate" element={<DictationPage />} />
        <Route path="clauses" element={<ClausesPage />} />
        <Route path="signin" element={<SignInPage />} />
        <Route path="admin" element={<AdminPage />} />
      </Route>
    </Routes>
  )
}
