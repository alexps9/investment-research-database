/**
 * SearchBar Component Tests - TDD Approach
 *
 * Coverage Target: ≥ 80%
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchBar from '@/components/SearchBar'

// ============================================================================
// Test 1: Renders Search Input
// ============================================================================

describe('SearchBar Component', () => {
  it('renders search input with label', () => {
    // Arrange
    const mockOnSearch = jest.fn()

    // Act
    render(<SearchBar onSearch={mockOnSearch} />)

    // Assert
    const label = screen.getByText('Search Academic Papers')
    const input = screen.getByLabelText('Search academic papers')
    const button = screen.getByRole('button', { name: 'Search' })

    expect(label).toBeInTheDocument()
    expect(input).toBeInTheDocument()
    expect(button).toBeInTheDocument()
  })

  // ==========================================================================
  // Test 2: Handles User Input
  // ==========================================================================

  it('updates input value when user types', async () => {
    const mockOnSearch = jest.fn()
    const user = userEvent.setup()

    render(<SearchBar onSearch={mockOnSearch} />)

    const input = screen.getByLabelText('Search academic papers') as HTMLInputElement

    // Type query
    await user.type(input, 'machine learning')

    expect(input.value).toBe('machine learning')
  })

  // ==========================================================================
  // Test 3: Calls onSearch on Submit
  // ==========================================================================

  it('calls onSearch with query when form is submitted', async () => {
    const mockOnSearch = jest.fn()
    const user = userEvent.setup()

    render(<SearchBar onSearch={mockOnSearch} />)

    const input = screen.getByLabelText('Search academic papers')
    const button = screen.getByRole('button', { name: 'Search' })

    // Type and submit
    await user.type(input, 'neural networks')
    await user.click(button)

    expect(mockOnSearch).toHaveBeenCalledWith('neural networks')
    expect(mockOnSearch).toHaveBeenCalledTimes(1)
  })

  // ==========================================================================
  // Test 4: Prevents Empty Query Submission
  // ==========================================================================

  it('does not call onSearch for empty query', async () => {
    const mockOnSearch = jest.fn()
    const user = userEvent.setup()

    render(<SearchBar onSearch={mockOnSearch} />)

    const button = screen.getByRole('button', { name: 'Search' })

    // Try to submit empty
    await user.click(button)

    expect(mockOnSearch).not.toHaveBeenCalled()
  })

  // ==========================================================================
  // Test 5: Trims Whitespace
  // ==========================================================================

  it('trims whitespace from query', async () => {
    const mockOnSearch = jest.fn()
    const user = userEvent.setup()

    render(<SearchBar onSearch={mockOnSearch} />)

    const input = screen.getByLabelText('Search academic papers')
    const button = screen.getByRole('button', { name: 'Search' })

    await user.type(input, '  deep learning  ')
    await user.click(button)

    expect(mockOnSearch).toHaveBeenCalledWith('deep learning')
  })

  // ==========================================================================
  // Test 6: Keyboard Shortcut (Cmd+K)
  // ==========================================================================

  it('focuses input on Cmd+K / Ctrl+K', () => {
    const mockOnSearch = jest.fn()

    render(<SearchBar onSearch={mockOnSearch} />)

    const input = screen.getByLabelText('Search academic papers')

    // Simulate Cmd+K (Mac)
    fireEvent.keyDown(window, { key: 'k', metaKey: true })

    expect(document.activeElement).toBe(input)
  })

  // ==========================================================================
  // Test 7: Loading State
  // ==========================================================================

  it('disables input and button when loading', () => {
    const mockOnSearch = jest.fn()

    render(<SearchBar onSearch={mockOnSearch} isLoading={true} />)

    const input = screen.getByLabelText('Search academic papers') as HTMLInputElement
    const button = screen.getByRole('button', { name: 'Search' })

    expect(input.disabled).toBe(true)
    expect(button.disabled).toBe(true)
    expect(button).toHaveTextContent('Searching...')
  })

  // ==========================================================================
  // Test 8: Initial Value
  // ==========================================================================

  it('renders with initial value', () => {
    const mockOnSearch = jest.fn()

    render(<SearchBar onSearch={mockOnSearch} initialValue="quantum computing" />)

    const input = screen.getByLabelText('Search academic papers') as HTMLInputElement

    expect(input.value).toBe('quantum computing')
  })

  // ==========================================================================
  // Test 9: Accessibility (ARIA)
  // ==========================================================================

  it('has proper ARIA labels', () => {
    const mockOnSearch = jest.fn()

    render(<SearchBar onSearch={mockOnSearch} />)

    const form = screen.getByRole('search')
    const input = screen.getByLabelText('Search academic papers')

    expect(form).toBeInTheDocument()
    expect(input).toHaveAttribute('aria-label', 'Search academic papers')
  })
})
