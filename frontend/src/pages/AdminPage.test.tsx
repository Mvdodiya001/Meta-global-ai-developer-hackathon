import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AdminPage } from './AdminPage'

describe('AdminPage', () => {
  it('loads the internal overview through the API client', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>,
    )
    expect(
      await screen.findByRole('heading', { name: /Internal overview/i }),
    ).toBeInTheDocument()
    // Regression: the page used a raw relative fetch('/api/admin/overview')
    // with no API base and no bearer token, which always failed on the
    // split (Vercel + API server) deployment.
    expect(await screen.findByText('Estimated model spend')).toBeInTheDocument()
    expect(screen.getByText('Answers so far')).toBeInTheDocument()
    expect(screen.getByText('Facts by confirmation state')).toBeInTheDocument()
  })
})
