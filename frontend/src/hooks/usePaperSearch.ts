/**
 * usePaperSearch Hook
 *
 * Manages paper search state and API calls
 *
 * Error Handling Philosophy:
 * - All errors are surfaced to UI
 * - No silent failures
 * - Clear, actionable error messages
 */

import { useState, useCallback } from 'react'
import { searchPapers, APIError } from '@/lib/api-client'
import type { GraphResponse } from '@/types/api'

export interface UsePaperSearchResult {
  /** Current search query */
  query: string
  /** Loading state */
  isLoading: boolean
  /** Error state (null if no error) */
  error: string | null
  /** Graph data (null if no data) */
  data: GraphResponse | null
  /** Execute search */
  search: (query: string, limit?: number) => Promise<void>
  /** Clear results */
  clear: () => void
}

export function usePaperSearch(): UsePaperSearchResult {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<GraphResponse | null>(null)

  const search = useCallback(async (searchQuery: string, limit: number = 50) => {
    // Reset state at the start of each search
    setQuery(searchQuery)
    setIsLoading(true)
    setError(null)
    setData(null)

    try {
      const response = await searchPapers(searchQuery, limit)
      setData(response)
    } catch (err) {
      // Transparent error handling - NO SILENT FAILURES
      if (err instanceof APIError) {
        setError(err.message)
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clear = useCallback(() => {
    setQuery('')
    setError(null)
    setData(null)
  }, [])

  return {
    query,
    isLoading,
    error,
    data,
    search,
    clear
  }
}
