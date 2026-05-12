/**
 * usePaperSearch Hook Tests - TDD Approach
 *
 * Coverage Target: ≥ 85%
 *
 * Core Principle: Transparent Error Handling
 * - All errors must be surfaced to UI
 * - No silent failures
 * - Clear, actionable error messages
 */

import { renderHook, waitFor } from '@testing-library/react'
import { usePaperSearch } from '@/hooks/usePaperSearch'
import * as apiClient from '@/lib/api-client'
import type { GraphResponse } from '@/types/api'

// Mock the searchPapers function
jest.mock('@/lib/api-client', () => ({
  ...jest.requireActual('@/lib/api-client'),
  searchPapers: jest.fn(),
}))

describe('usePaperSearch Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ==========================================================================
  // Test 1: Initializes with Empty State
  // ==========================================================================

  it('initializes with empty state', () => {
    const { result } = renderHook(() => usePaperSearch())

    expect(result.current.query).toBe('')
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBeNull()
    expect(typeof result.current.search).toBe('function')
    expect(typeof result.current.clear).toBe('function')
  })

  // ==========================================================================
  // Test 2: Fetches Data Successfully
  // ==========================================================================

  it('fetches data successfully', async () => {
    const mockData: GraphResponse = {
      nodes: [
        {
          id: 'W1',
          title: 'Machine Learning Paper',
          cited_by_count: 100,
          publication_year: 2020,
          community: 0
        }
      ],
      links: [],
      metadata: {
        total_nodes: 1,
        total_links: 0,
        communities: 1
      }
    }

    ;(apiClient.searchPapers as jest.Mock).mockResolvedValue(mockData)

    const { result } = renderHook(() => usePaperSearch())

    // Execute search
    await result.current.search('machine learning', 50)

    // Wait for async operations to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Verify successful state
    expect(result.current.query).toBe('machine learning')
    expect(result.current.data).toEqual(mockData)
    expect(result.current.error).toBeNull()
    expect(apiClient.searchPapers).toHaveBeenCalledWith('machine learning', 50)
    expect(apiClient.searchPapers).toHaveBeenCalledTimes(1)
  })

  // ==========================================================================
  // Test 3: Handles API Errors Transparently (CRITICAL TEST)
  // ==========================================================================

  it('handles API errors transparently', async () => {
    const mockError = new apiClient.APIError(
      'Failed to fetch papers: Network timeout',
      0,
      'Connection refused'
    )

    ;(apiClient.searchPapers as jest.Mock).mockRejectedValue(mockError)

    const { result } = renderHook(() => usePaperSearch())

    // Execute search that will fail - MUST await
    await result.current.search('test query')

    // Wait for async operations to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Verify spy was called
    expect(apiClient.searchPapers).toHaveBeenCalledWith('test query', 50)

    // CRITICAL: Error MUST be surfaced, not hidden
    expect(result.current.error).toBe('Failed to fetch papers: Network timeout')
    expect(result.current.data).toBeNull()
    expect(result.current.query).toBe('test query')
  })

  // ==========================================================================
  // Test 4: Clears Results
  // ==========================================================================

  it('clears results', async () => {
    const mockData: GraphResponse = {
      nodes: [],
      links: [],
      metadata: { total_nodes: 0, total_links: 0, communities: 0 }
    }

    ;(apiClient.searchPapers as jest.Mock).mockResolvedValue(mockData)

    const { result } = renderHook(() => usePaperSearch())

    // First, perform a search
    result.current.search('test', 50)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Verify data is present
    expect(result.current.data).toEqual(mockData)
    expect(result.current.query).toBe('test')

    // Now clear - wrap in act
    await waitFor(() => {
      result.current.clear()
    })

    // Verify everything is cleared
    expect(result.current.query).toBe('')
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBeNull()
    expect(result.current.isLoading).toBe(false)
  })

  // ==========================================================================
  // Test 5: Handles Standard Error Objects
  // ==========================================================================

  it('handles standard Error objects', async () => {
    const standardError = new Error('Something unexpected happened')

    ;(apiClient.searchPapers as jest.Mock).mockRejectedValue(standardError)

    const { result } = renderHook(() => usePaperSearch())

    await result.current.search('query')

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBe('Something unexpected happened')
    expect(result.current.data).toBeNull()
  })

  // ==========================================================================
  // Test 6: Handles Non-Error Rejections
  // ==========================================================================

  it('handles non-error rejections', async () => {
    ;(apiClient.searchPapers as jest.Mock).mockRejectedValue('Unknown error')

    const { result } = renderHook(() => usePaperSearch())

    await result.current.search('query')

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBe('An unexpected error occurred. Please try again.')
    expect(result.current.data).toBeNull()
  })

  // ==========================================================================
  // Test 7: Loading State Management
  // ==========================================================================

  it('manages loading state correctly', async () => {
    const mockData: GraphResponse = {
      nodes: [],
      links: [],
      metadata: { total_nodes: 0, total_links: 0, communities: 0 }
    }

    // Create a promise we can control
    let resolveSearch: (value: GraphResponse) => void
    const searchPromise = new Promise<GraphResponse>((resolve) => {
      resolveSearch = resolve
    })

    ;(apiClient.searchPapers as jest.Mock).mockReturnValue(searchPromise)

    const { result } = renderHook(() => usePaperSearch())

    // Start search
    result.current.search('test')

    // Wait for loading to be true
    await waitFor(() => {
      expect(result.current.isLoading).toBe(true)
    })

    expect(result.current.data).toBeNull()
    expect(result.current.error).toBeNull()

    // Resolve the promise
    resolveSearch!(mockData)

    // Should no longer be loading
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.data).toEqual(mockData)
  })

  // ==========================================================================
  // Test 8: Resets State on New Search
  // ==========================================================================

  it('resets state on new search', async () => {
    const firstData: GraphResponse = {
      nodes: [{ id: 'W1', title: 'First', cited_by_count: 10, publication_year: 2020 }],
      links: [],
      metadata: { total_nodes: 1, total_links: 0, communities: 1 }
    }

    const secondData: GraphResponse = {
      nodes: [{ id: 'W2', title: 'Second', cited_by_count: 20, publication_year: 2021 }],
      links: [],
      metadata: { total_nodes: 1, total_links: 0, communities: 1 }
    }

    ;(apiClient.searchPapers as jest.Mock)
      .mockResolvedValueOnce(firstData)
      .mockResolvedValueOnce(secondData)

    const { result } = renderHook(() => usePaperSearch())

    // First search
    await result.current.search('first query')

    await waitFor(() => {
      expect(result.current.data).toEqual(firstData)
    })

    // Second search should reset state
    await result.current.search('second query')

    await waitFor(() => {
      expect(result.current.data).toEqual(secondData)
    })

    expect(result.current.query).toBe('second query')
    expect(result.current.error).toBeNull()
  })
})
