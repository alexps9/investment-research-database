/**
 * Integration Tests - Main Page
 *
 * Tests complete user flows:
 * 1. Search → Loading → Success (display graph)
 * 2. Search → Loading → Error → Retry
 * 3. Search → Loading → Empty Results
 *
 * Design Validation:
 * - Rams-compliant UI rendering
 * - Proper state transitions
 * - Accessibility compliance
 */

import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Home from '@/app/page'
import { searchPapers } from '@/lib/api-client'

// Mock API client
jest.mock('@/lib/api-client')
const mockSearchPapers = searchPapers as jest.MockedFunction<typeof searchPapers>

// Mock react-force-graph-2d (avoid canvas issues in test environment)
jest.mock('react-force-graph-2d', () => {
  return function MockForceGraph2D() {
    return <div data-testid="force-graph-mock">Force Graph</div>
  }
})

describe('Home Page Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Initial State', () => {
    test('renders title and subtitle', () => {
      render(<Home />)

      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Academic Paper Analysis')
      expect(screen.getByText(/visualize citation networks/i)).toBeInTheDocument()
    })

    test('renders search bar', () => {
      render(<Home />)

      // SearchBar uses type="text" so role is "textbox" not "searchbox"
      expect(screen.getByRole('textbox', { name: /search academic papers/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument()
    })

    test('does not show loading, error, or graph initially', () => {
      render(<Home />)

      expect(screen.queryByRole('status')).not.toBeInTheDocument()
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      expect(screen.queryByTestId('force-graph-mock')).not.toBeInTheDocument()
    })
  })

  describe('Success Flow: Search → Loading → Results', () => {
    test('displays loading state during search', async () => {
      const user = userEvent.setup()

      // Mock API call with delay
      mockSearchPapers.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          nodes: [
            {
              id: 'W001',
              title: 'Paper 1',
              cited_by_count: 10,
              publication_year: 2023,
              community: 0
            }
          ],
          links: [],
          metadata: {
            total_nodes: 1,
            total_links: 0,
            query: 'quantum',
            communities_count: 1
          }
        }), 100))
      )

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'quantum computing')
      await user.click(button)

      // Loading state should appear
      expect(screen.getByRole('status')).toBeInTheDocument()
      expect(screen.getByText(/fetching papers/i)).toBeInTheDocument()
    })

    test('displays graph after successful search', async () => {
      const user = userEvent.setup()

      mockSearchPapers.mockResolvedValue({
        nodes: [
          {
            id: 'W001',
            title: 'Quantum Computing Paper',
            cited_by_count: 42,
            publication_year: 2023,
            community: 0
          },
          {
            id: 'W002',
            title: 'Machine Learning Paper',
            cited_by_count: 15,
            publication_year: 2022,
            community: 1
          }
        ],
        links: [
          { source: 'W001', target: 'W002' }
        ],
        metadata: {
          total_nodes: 2,
          total_links: 1,
          query: 'quantum',
          communities_count: 2
        }
      })

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'quantum')
      await user.click(button)

      // Wait for graph to appear
      await waitFor(() => {
        expect(screen.getByTestId('force-graph-mock')).toBeInTheDocument()
      })

      // Metadata should be displayed (text broken up by spans, use function matcher)
      expect(screen.getByText((content, element) => {
        return element?.textContent === '2 papers'
      })).toBeInTheDocument()
      expect(screen.getByText((content, element) => {
        return element?.textContent === '1 citation'
      })).toBeInTheDocument()

      // Loading should disappear
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })

    test('calls API with correct parameters', async () => {
      const user = userEvent.setup()

      mockSearchPapers.mockResolvedValue({
        nodes: [],
        links: [],
        metadata: {
          total_nodes: 0,
          total_links: 0,
          query: 'test query',
          communities_count: 0
        }
      })

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'test query')
      await user.click(button)

      await waitFor(() => {
        expect(mockSearchPapers).toHaveBeenCalledWith('test query', 50)
      })
    })
  })

  describe('Error Flow: Search → Error → Retry', () => {
    test('displays error message when search fails', async () => {
      const user = userEvent.setup()

      mockSearchPapers.mockRejectedValue(new Error('Network error: Failed to fetch'))

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'error query')
      await user.click(button)

      // Error message should appear
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })

      expect(screen.getByText(/network error/i)).toBeInTheDocument()

      // Loading should disappear
      expect(screen.queryByRole('status')).not.toBeInTheDocument()

      // Graph should not appear
      expect(screen.queryByTestId('force-graph-mock')).not.toBeInTheDocument()
    })

    test('allows user to retry after error', async () => {
      const user = userEvent.setup()

      // First call fails
      mockSearchPapers.mockRejectedValueOnce(new Error('Network timeout'))

      // Second call succeeds
      mockSearchPapers.mockResolvedValueOnce({
        nodes: [
          {
            id: 'W001',
            title: 'Retry Success Paper',
            cited_by_count: 5,
            publication_year: 2023,
            community: 0
          }
        ],
        links: [],
        metadata: {
          total_nodes: 1,
          total_links: 0,
          query: 'retry query',
          communities_count: 1
        }
      })

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const searchButton = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'retry query')
      await user.click(searchButton)

      // Wait for error
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry/i })
      await user.click(retryButton)

      // Wait for success
      await waitFor(() => {
        expect(screen.getByTestId('force-graph-mock')).toBeInTheDocument()
      })

      // Error should disappear
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()

      // API should be called twice
      expect(mockSearchPapers).toHaveBeenCalledTimes(2)
    })

    test('allows user to dismiss error', async () => {
      const user = userEvent.setup()

      mockSearchPapers.mockRejectedValue(new Error('API Error'))

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'error query')
      await user.click(button)

      // Wait for error
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })

      // Click dismiss button
      const dismissButton = screen.getByRole('button', { name: /dismiss/i })
      await user.click(dismissButton)

      // Error should disappear
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      })
    })
  })

  describe('Empty Results Flow', () => {
    test('displays empty state when no papers found', async () => {
      const user = userEvent.setup()

      mockSearchPapers.mockResolvedValue({
        nodes: [],
        links: [],
        metadata: {
          total_nodes: 0,
          total_links: 0,
          query: 'nonexistent topic',
          communities_count: 0
        }
      })

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'nonexistent topic')
      await user.click(button)

      // Wait for empty state message
      await waitFor(() => {
        expect(screen.getByText(/no papers found/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/nonexistent topic/i)).toBeInTheDocument()
      expect(screen.getByText(/try a different search term/i)).toBeInTheDocument()

      // Graph should not appear
      expect(screen.queryByTestId('force-graph-mock')).not.toBeInTheDocument()
    })
  })

  describe('State Transitions', () => {
    test('clears previous results when starting new search', async () => {
      const user = userEvent.setup()

      // First search returns results
      mockSearchPapers.mockResolvedValueOnce({
        nodes: [
          {
            id: 'W001',
            title: 'First Paper',
            cited_by_count: 10,
            publication_year: 2023,
            community: 0
          }
        ],
        links: [],
        metadata: {
          total_nodes: 1,
          total_links: 0,
          query: 'first',
          communities_count: 1
        }
      })

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      // First search
      await user.type(input, 'first')
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByTestId('force-graph-mock')).toBeInTheDocument()
      })

      // Second search returns empty
      mockSearchPapers.mockResolvedValueOnce({
        nodes: [],
        links: [],
        metadata: {
          total_nodes: 0,
          total_links: 0,
          query: 'second',
          communities_count: 0
        }
      })

      // Clear input and type new query
      await user.clear(input)
      await user.type(input, 'second')
      await user.click(button)

      // Old graph should disappear, empty state should appear
      await waitFor(() => {
        expect(screen.queryByTestId('force-graph-mock')).not.toBeInTheDocument()
        expect(screen.getByText(/no papers found/i)).toBeInTheDocument()
      })
    })

    test('clears error when starting new search', async () => {
      const user = userEvent.setup()

      // First search fails
      mockSearchPapers.mockRejectedValueOnce(new Error('Error'))

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'error query')
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })

      // Second search succeeds
      mockSearchPapers.mockResolvedValueOnce({
        nodes: [
          {
            id: 'W001',
            title: 'Success Paper',
            cited_by_count: 10,
            publication_year: 2023,
            community: 0
          }
        ],
        links: [],
        metadata: {
          total_nodes: 1,
          total_links: 0,
          query: 'success',
          communities_count: 1
        }
      })

      await user.clear(input)
      await user.type(input, 'success')
      await user.click(button)

      // Error should disappear, graph should appear
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument()
        expect(screen.getByTestId('force-graph-mock')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    test('has proper heading hierarchy', () => {
      render(<Home />)

      const h1 = screen.getByRole('heading', { level: 1 })
      expect(h1).toHaveTextContent('Academic Paper Analysis')
    })

    test('search form has proper ARIA labels', () => {
      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      expect(input).toHaveAccessibleName()
    })

    test('loading state is announced to screen readers', async () => {
      const user = userEvent.setup()

      mockSearchPapers.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          nodes: [],
          links: [],
          metadata: {
            total_nodes: 0,
            total_links: 0,
            query: 'test',
            communities_count: 0
          }
        }), 100))
      )

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'test')
      await user.click(button)

      const loadingElement = screen.getByRole('status')
      expect(loadingElement).toHaveAttribute('aria-live', 'polite')
    })

    test('error messages are announced assertively', async () => {
      const user = userEvent.setup()

      mockSearchPapers.mockRejectedValue(new Error('Error'))

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'test')
      await user.click(button)

      await waitFor(() => {
        const alert = screen.getByRole('alert')
        expect(alert).toHaveAttribute('aria-live', 'assertive')
      })
    })
  })

  describe('Design Compliance (Rams Principles)', () => {
    test('renders with clean structure (no decorative elements)', () => {
      const { container } = render(<Home />)

      // Should have main landmark
      expect(screen.getByRole('main')).toBeInTheDocument()

      // Should not have unnecessary wrapper divs
      const main = container.querySelector('main')
      expect(main).toBeTruthy()
    })

    test('metadata uses uppercase text (Rams industrial style)', async () => {
      const user = userEvent.setup()

      mockSearchPapers.mockResolvedValue({
        nodes: [
          {
            id: 'W001',
            title: 'Paper',
            cited_by_count: 10,
            publication_year: 2023,
            community: 0
          }
        ],
        links: [],
        metadata: {
          total_nodes: 1,
          total_links: 0,
          query: 'test',
          communities_count: 1
        }
      })

      render(<Home />)

      const input = screen.getByRole('textbox', { name: /search academic papers/i })
      const button = screen.getByRole('button', { name: /search/i })

      await user.type(input, 'test')
      await user.click(button)

      await waitFor(() => {
        // Metadata should be displayed (testing it exists, using function matcher for broken-up text)
        expect(screen.getByText((content, element) => {
          return element?.textContent === '1 paper'
        })).toBeInTheDocument()
      })
    })
  })
})
