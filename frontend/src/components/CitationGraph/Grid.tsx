import {
  BEFORE_2023_W,
  END_YEAR,
  LANE_H,
  LANE_IDS,
  LANE_LABEL_W,
  Q_W,
  QUARTERS_PER_YEAR,
  START_YEAR,
  SUB_LANE_H,
  SUB_LANES,
} from '@/lib/citation-graph/constants'
import { CANVAS_W, LANES_BAND_H } from '@/lib/citation-graph/layout'
import styles from './CitationGraph.module.css'

export function Grid() {
  // Vertical gutters: one per year boundary (thicker) + per quarter (lighter)
  const quarterLines: number[] = []
  const yearLines: number[] = []
  for (let y = START_YEAR; y <= END_YEAR; y++) {
    for (let q = 1; q <= QUARTERS_PER_YEAR; q++) {
      const yearOffset = y - START_YEAR
      const idx = yearOffset * QUARTERS_PER_YEAR + (q - 1)
      const x = LANE_LABEL_W + BEFORE_2023_W + idx * Q_W
      if (q === 1) yearLines.push(x)
      else quarterLines.push(x)
    }
  }

  return (
    <div className={styles.grid} style={{ width: CANVAS_W, height: LANES_BAND_H }}>
      {/* Before-2023 divider: thick line right of the aggregation column */}
      <div
        className={styles.gridBefore2023Divider}
        style={{ left: LANE_LABEL_W + BEFORE_2023_W, height: LANES_BAND_H }}
      />
      {/* Year lines */}
      {yearLines.map((x) => (
        <div
          key={`y-${x}`}
          className={styles.gridYearLine}
          style={{ left: x, height: LANES_BAND_H }}
        />
      ))}
      {/* Quarter lines */}
      {quarterLines.map((x) => (
        <div
          key={`q-${x}`}
          className={styles.gridQuarterLine}
          style={{ left: x, height: LANES_BAND_H }}
        />
      ))}
      {/* Horizontal lane and sub-lane dividers */}
      {LANE_IDS.map((laneId, laneIdx) => {
        const laneTop = laneIdx * LANE_H
        return (
          <div key={laneId}>
            {/* Sub-lane dashed dividers within this lane (between A/B and B/C) */}
            {SUB_LANES.slice(0, -1).map((_, subIdx) => (
              <div
                key={`sub-${laneId}-${subIdx}`}
                className={styles.gridSubLaneDivider}
                style={{ top: laneTop + (subIdx + 1) * SUB_LANE_H }}
              />
            ))}
            {/* Solid lane divider below this lane (skip the last one) */}
            {laneIdx < LANE_IDS.length - 1 && (
              <div
                className={styles.gridLaneDivider}
                style={{ top: laneTop + LANE_H - 1 }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
