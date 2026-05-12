/**
 * Home page tests
 * TDD: Red → Green → Refactor
 */

import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

describe('Home Page', () => {
  it('renders the title', () => {
    render(<Home />)
    const title = screen.getByText('Academic Paper Analysis')
    expect(title).toBeInTheDocument()
  })

  it('renders the subtitle', () => {
    render(<Home />)
    const subtitle = screen.getByText(/Visualize citation networks/i)
    expect(subtitle).toBeInTheDocument()
  })

  it('renders search bar component', () => {
    render(<Home />)
    const searchInput = screen.getByPlaceholderText(/enter topic or keywords/i)
    expect(searchInput).toBeInTheDocument()
  })
})
