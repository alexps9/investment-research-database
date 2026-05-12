'use client'

import { useMemo } from 'react'
import type { GraphData } from '@/types/citation-graph'
import { LANES, Q_W, nowQuarter } from '@/lib/citation-graph/constants'
import {
  CANVAS_W,
  LANES_BAND_H,
  quarterCells,
  stackNodes,
} from '@/lib/citation-graph/layout'
import styles from './CitationGraph.module.css'
import { Header } from './Header'
import { Grid } from './Grid'
import { LaneLabels } from './LaneLabels'
import { Connections } from './Connections'
import { NodeLabels } from './NodeLabels'

interface Props {
  data: GraphData
  selectedId: string | null
  onSelect: (id: string | null) => void
}

export default function CitationGraph({ data, selectedId, onSelect }: Props) {
  const { year: nowY, quarter: nowQ } = useMemo(() => nowQuarter(), [])
  const cells = useMemo(() => quarterCells(nowY, nowQ), [nowY, nowQ])
  const stacked = useMemo(() => stackNodes(data.nodes), [data.nodes])

  // Highlighted link ids based on current selection.
  const highlightedLinks = useMemo(() => {
    if (!selectedId) return new Set<string>()
    return new Set(
      data.links
        .filter((l) => l.source === selectedId || l.target === selectedId)
        .map((l) => `${l.source}→${l.target}`),
    )
  }, [selectedId, data.links])

  const nowX = useMemo(() => {
    const cell = cells.find((c) => c.isNow)
    if (!cell) return null
    return cell.x + Q_W / 2
  }, [cells])

  return (
    <div className={styles.root}>
      <div className={styles.scroll}>
        <div style={{ width: CANVAS_W, minWidth: CANVAS_W }}>
          <Header cells={cells} />
          <div
            className={styles.canvas}
            style={{ width: CANVAS_W, height: LANES_BAND_H, position: 'relative' }}
          >
            <Grid />
            <LaneLabels />
            <Connections
              nodes={stacked}
              links={data.links}
              highlighted={highlightedLinks}
              hasSelection={selectedId !== null}
            />
            {nowX !== null && (
              <>
                <div
                  className={styles.nowLine}
                  style={{ left: nowX, height: LANES_BAND_H }}
                />
                <div className={styles.nowLabel} style={{ left: nowX, top: 2 }}>
                  NOW
                </div>
              </>
            )}
            <div
              className={styles.nodeLayer}
              style={{ width: CANVAS_W, height: LANES_BAND_H }}
            >
              {stacked.map((n) => {
                const isSelected = n.id === selectedId
                const className = [
                  styles.node,
                  n.alpha === 'high' ? styles.nodeAlphaHigh : '',
                  isSelected ? styles.nodeSelected : '',
                ]
                  .filter(Boolean)
                  .join(' ')
                const lane = LANES[n.lane]
                return (
                  <button
                    key={n.id}
                    type="button"
                    className={className}
                    style={{
                      left: n._x,
                      top: n._y,
                      width: n._r * 2,
                      height: n._r * 2,
                      background: n.tier === 1 ? lane.color : lane.fill,
                      borderColor: lane.color,
                    }}
                    title={`${n.title} · ${n.year} Q${n.quarter} · ${n.cited_by_count.toLocaleString()} cites`}
                    onClick={(e) => {
                      e.stopPropagation()
                      onSelect(n.id === selectedId ? null : n.id)
                    }}
                  />
                )
              })}
            </div>
            <NodeLabels nodes={stacked} selectedId={selectedId} />
          </div>
        </div>
      </div>
    </div>
  )
}
