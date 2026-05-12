import type { QuarterCell } from '@/lib/citation-graph/layout'
import {
  BEFORE_2023_W,
  END_YEAR,
  LANE_LABEL_W,
  Q_W,
  QUARTERS_PER_YEAR,
  START_YEAR,
} from '@/lib/citation-graph/constants'
import styles from './CitationGraph.module.css'

export function Header({ cells }: { cells: QuarterCell[] }) {
  const yearSpanPx = QUARTERS_PER_YEAR * Q_W
  const years: number[] = []
  for (let y = START_YEAR; y <= END_YEAR; y++) years.push(y)

  return (
    <div className={styles.header}>
      {/* Row 1: Year labels */}
      <div className={styles.headerRow}>
        <div
          className={styles.headerLabelCell}
          style={{ width: LANE_LABEL_W, height: '100%' }}
        >
          LANE
        </div>
        <div
          className={styles.headerBefore2023}
          style={{ width: BEFORE_2023_W, height: '100%' }}
        >
          Before 2023
        </div>
        {years.map((y) => (
          <div
            key={y}
            className={styles.yearCell}
            style={{ width: yearSpanPx, height: '100%' }}
          >
            {y}
          </div>
        ))}
      </div>
      {/* Row 2: Quarter labels */}
      <div className={styles.headerRow}>
        <div
          className={styles.headerLabelCell}
          style={{ width: LANE_LABEL_W, height: '100%' }}
        />
        <div
          className={styles.headerBefore2023}
          style={{ width: BEFORE_2023_W, height: '100%' }}
        />
        {cells.map((c) => (
          <div
            key={`${c.year}-${c.quarter}`}
            className={
              c.isNow
                ? `${styles.quarterCell} ${styles.quarterCellNow}`
                : styles.quarterCell
            }
            style={{ width: Q_W, height: '100%' }}
          >
            Q{c.quarter}
          </div>
        ))}
      </div>
    </div>
  )
}
