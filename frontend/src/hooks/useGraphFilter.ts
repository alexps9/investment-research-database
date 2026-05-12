'use client'

import { useMemo, useState, useCallback } from 'react'
import type { GraphResponse, Node } from '@/types/api'

export interface FilterState {
  yearRange: [number, number]
  minCitations: number
}

export interface UseGraphFilterResult {
  filteredData: GraphResponse | null
  filters: FilterState
  yearBounds: [number, number]
  maxCitations: number
  setYearRange: (range: [number, number]) => void
  setMinCitations: (min: number) => void
  resetFilters: () => void
  topNodes: Node[]
}

export function useGraphFilter(data: GraphResponse | null): UseGraphFilterResult {
  const yearBounds = useMemo<[number, number]>(() => {
    if (!data || data.nodes.length === 0) return [2000, 2026]
    // Exclude placeholder nodes (year=1900) from bounds calculation
    const years = data.nodes.map(n => n.publication_year).filter(y => y > 1950)
    if (years.length === 0) return [2000, 2026]
    return [Math.min(...years), Math.max(...years)]
  }, [data])

  const maxCitations = useMemo(() => {
    if (!data || data.nodes.length === 0) return 100
    return Math.max(...data.nodes.map(n => n.cited_by_count))
  }, [data])

  const [filters, setFilters] = useState<FilterState>({
    yearRange: yearBounds,
    minCitations: 0,
  })

  // Reset filters when data changes
  useMemo(() => {
    setFilters({ yearRange: yearBounds, minCitations: 0 })
  }, [yearBounds])

  const setYearRange = useCallback((range: [number, number]) => {
    setFilters(prev => ({ ...prev, yearRange: range }))
  }, [])

  const setMinCitations = useCallback((min: number) => {
    setFilters(prev => ({ ...prev, minCitations: min }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters({ yearRange: yearBounds, minCitations: 0 })
  }, [yearBounds])

  const topNodes = useMemo(() => {
    if (!data) return []
    return [...data.nodes]
      .sort((a, b) => b.cited_by_count - a.cited_by_count)
      .slice(0, 10)
  }, [data])

  const filteredData = useMemo(() => {
    if (!data) return null

    const visibleNodeIds = new Set<string>()
    const filteredNodes = data.nodes.filter(node => {
      const inYear = node.publication_year >= filters.yearRange[0] &&
                     node.publication_year <= filters.yearRange[1]
      const aboveCitations = node.cited_by_count >= filters.minCitations
      if (inYear && aboveCitations) {
        visibleNodeIds.add(node.id)
        return true
      }
      return false
    })

    const filteredLinks = data.links.filter(
      link => visibleNodeIds.has(link.source) && visibleNodeIds.has(link.target)
    )

    return {
      nodes: filteredNodes,
      links: filteredLinks,
      metadata: {
        ...data.metadata,
        total_nodes: filteredNodes.length,
        total_links: filteredLinks.length,
      },
    }
  }, [data, filters])

  return {
    filteredData,
    filters,
    yearBounds,
    maxCitations,
    setYearRange,
    setMinCitations,
    resetFilters,
    topNodes,
  }
}
