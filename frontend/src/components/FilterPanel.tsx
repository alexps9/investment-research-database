'use client'

import { useCallback, useMemo } from 'react'
import styles from './FilterPanel.module.css'

// Log scale ticks for citation filter
const CITATION_TICKS = [0, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 50000]

function findClosestTickIndex(value: number): number {
  let closest = 0
  let minDiff = Math.abs(CITATION_TICKS[0] - value)
  for (let i = 1; i < CITATION_TICKS.length; i++) {
    const diff = Math.abs(CITATION_TICKS[i] - value)
    if (diff < minDiff) {
      minDiff = diff
      closest = i
    }
  }
  return closest
}

export interface FilterPanelProps {
  yearRange: [number, number]
  yearBounds: [number, number]
  minCitations: number
  maxCitations: number
  onYearChange: (range: [number, number]) => void
  onCitationsChange: (min: number) => void
  onReset: () => void
  totalNodes: number
  filteredNodes: number
}

export default function FilterPanel({
  yearRange,
  yearBounds,
  minCitations,
  maxCitations,
  onYearChange,
  onCitationsChange,
  onReset,
  totalNodes,
  filteredNodes,
}: FilterPanelProps) {
  // Find the max useful tick index based on data
  const maxTickIndex = useMemo(() => {
    for (let i = CITATION_TICKS.length - 1; i >= 0; i--) {
      if (CITATION_TICKS[i] <= maxCitations) return Math.min(i + 1, CITATION_TICKS.length - 1)
    }
    return CITATION_TICKS.length - 1
  }, [maxCitations])

  const currentTickIndex = findClosestTickIndex(minCitations)

  const handleYearMin = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value)
    onYearChange([val, Math.max(val, yearRange[1])])
  }, [yearRange, onYearChange])

  const handleYearMax = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value)
    onYearChange([Math.min(yearRange[0], val), val])
  }, [yearRange, onYearChange])

  const handleCitations = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value)
    onCitationsChange(CITATION_TICKS[idx] ?? 0)
  }, [onCitationsChange])

  const isFiltered = minCitations > 0 ||
    yearRange[0] > yearBounds[0] ||
    yearRange[1] < yearBounds[1]

  const citationLabel = minCitations >= 1000
    ? `${(minCitations / 1000).toFixed(minCitations % 1000 === 0 ? 0 : 1)}k`
    : String(minCitations)

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.title}>筛选条件</span>
        {isFiltered && (
          <button className={styles.resetBtn} onClick={onReset}>重置</button>
        )}
      </div>

      <div className={styles.filterGroup}>
        <label className={styles.label}>
          年份：{yearRange[0]} – {yearRange[1]}
        </label>
        <div className={styles.dualRange}>
          <input
            type="range"
            min={yearBounds[0]}
            max={yearBounds[1]}
            value={yearRange[0]}
            onChange={handleYearMin}
            className={styles.range}
          />
          <input
            type="range"
            min={yearBounds[0]}
            max={yearBounds[1]}
            value={yearRange[1]}
            onChange={handleYearMax}
            className={styles.range}
          />
        </div>
      </div>

      <div className={styles.filterGroup}>
        <label className={styles.label}>
          最低引用数：{citationLabel}
        </label>
        <input
          type="range"
          min={0}
          max={maxTickIndex}
          step={1}
          value={currentTickIndex}
          onChange={handleCitations}
          className={styles.range}
        />
        <div className={styles.tickLabels}>
          <span>0</span>
          <span>{CITATION_TICKS[Math.floor(maxTickIndex / 2)] ?? ''}</span>
          <span>{CITATION_TICKS[maxTickIndex] ?? ''}+</span>
        </div>
      </div>

      <div className={styles.stats}>
        {filteredNodes} / {totalNodes} 篇论文
      </div>
    </div>
  )
}
