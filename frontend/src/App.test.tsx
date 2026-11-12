import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('renders the frontend scaffold', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'Frontend scaffold ready' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Momentum AI')).toBeInTheDocument()
  })
})
