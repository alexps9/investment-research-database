'use client'

import { useState, useCallback } from 'react'
import { fetchSeedReport } from '@/lib/api-client'
import type { InsightReport } from '@/types/api'

export function useInsightReport() {
  const [report, setReport] = useState<InsightReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activePath, setActivePath] = useState<string | null>(null)

  const loadReport = useCallback(async (path: string) => {
    // Toggle off if clicking same path
    if (path === activePath) {
      setReport(null)
      setActivePath(null)
      return
    }

    setIsLoading(true)
    setError(null)
    setActivePath(path)

    try {
      const data = await fetchSeedReport(path)
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report')
      setReport(null)
    } finally {
      setIsLoading(false)
    }
  }, [activePath])

  const clearReport = useCallback(() => {
    setReport(null)
    setActivePath(null)
    setError(null)
  }, [])

  return { report, isLoading, error, activePath, loadReport, clearReport }
}
