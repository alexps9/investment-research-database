import { useMemo } from 'react'
import type { GraphLink, GraphNode } from '@/types/citation-graph'
import { CANVAS_W, LANES_BAND_H } from '@/lib/citation-graph/layout'
import styles from './CitationGraph.module.css'

interface PositionedNode extends GraphNode {
  _x: number
  _y: number
  _r: number
}

interface Props {
  nodes: PositionedNode[]
  links: GraphLink[]
  highlighted: Set<string>
  hasSelection: boolean
}

// Build a slight S-curve between two nodes so same-lane citations read cleanly.
function buildPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = x2 - x1
  const cx1 = x1 + dx * 0.35
  const cx2 = x1 + dx * 0.65
  return `M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`
}

export function Connections({ nodes, links, highlighted, hasSelection }: Props) {
  const byId = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes])

  return (
    <svg
      className={styles.connections}
      width={CANVAS_W}
      height={LANES_BAND_H}
      viewBox={`0 0 ${CANVAS_W} ${LANES_BAND_H}`}
    >
      {links.map((l) => {
        const s = byId.get(l.source)
        const t = byId.get(l.target)
        if (!s || !t) return null
        const key = `${l.source}→${l.target}`
        const sameLane = s.lane === t.lane
        const isHi = highlighted.has(key)
        const className = [
          sameLane ? styles.linkSameLane : styles.linkCrossLane,
          isHi ? styles.linkHighlighted : '',
          hasSelection && !isHi ? styles.linkDimmed : '',
        ]
          .filter(Boolean)
          .join(' ')
        return <path key={key} className={className} d={buildPath(s._x, s._y, t._x, t._y)} />
      })}
    </svg>
  )
}
