'use client'

import { useEffect, useState } from 'react'
import styles from './page.module.css'

interface Lane { id: string; title: string; subtitle: string; color: string }
interface Row { id: string; lane: string; title: string; subtitle: string }
interface Paper {
  id: string; title: string; year: number; quarter: number
  paradigm: string; layer: string; lane: string; row: string
  path: string; size: string; builds_on: string[]
}
interface Mutation { summary: string; detail: string; bottleneck?: string; result?: string }
interface Iteration {
  id: string; title: string; subtitle: string; path: string; row: string
  papers: string[]
  mutations: Record<string, Mutation>
}
interface MapData { lanes: Lane[]; rows: Row[]; papers: Paper[]; iterations: Iteration[] }

const COLORS: Record<string, string> = {
  attention_native: '#475569',
  post_attention: '#2563EB',
  sparse_long: '#0D9488',
  conditional: '#DC2626',
  reasoning: '#EA580C',
}

const LAYER_SHAPES: Record<string, string> = {
  arch: 'circle', sys: 'square', infer: 'diamond', train: 'triangle', memory: 'hexagon',
}

function qToX(year: number, quarter: number): number {
  return ((year - 2023) * 4 + (quarter - 1)) / 16 * 100
}

function getNodeSize(size: string): number {
  return size === 'lg' ? 10 : size === 'md' ? 7 : 5
}

// ─── Iteration View ─────────────────────────────────────────────

function IterationView({ iteration, papers, lanes, rows, onBack }: {
  iteration: Iteration
  papers: Paper[]
  lanes: Lane[]
  rows: Row[]
  onBack: () => void
}) {
  const row = rows.find(r => r.id === iteration.row)
  const lane = lanes.find(l => l.id === row?.lane)
  const iterPapers = iteration.papers.map(id => papers.find(p => p.id === id)).filter(Boolean) as Paper[]

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.breadcrumb}>
          <button onClick={onBack} className={styles.backBtn}>← Back</button>
          <span className={styles.breadcrumbSep}>›</span>
          <span style={{ color: lane?.color }}>{lane?.title}</span>
          <span className={styles.breadcrumbSep}>›</span>
          <span className={styles.breadcrumbCurrent}>{iteration.title}</span>
        </div>
      </header>

      <div className={styles.iterContent}>
        <div className={styles.iterTitle}>
          <h2>{iteration.title}</h2>
          <p>{iteration.subtitle}</p>
        </div>

        {/* Timeline axis */}
        <div className={styles.iterTimeline}>
          {['2023', '2024', '2025', '2026'].map(y => (
            <div key={y} className={styles.iterYear}>
              <div className={styles.iterYearLabel}>{y}</div>
              <div className={styles.iterQuarters}>
                {['Q1','Q2','Q3','Q4'].map(q => <span key={q}>{q}</span>)}
              </div>
            </div>
          ))}
        </div>

        {/* Nodes on timeline */}
        <div className={styles.iterNodes}>
          {/* Connection lines */}
          <svg className={styles.iterSvg}>
            {iterPapers.map((paper, i) => {
              if (i === 0) return null
              const prev = iterPapers[i - 1]
              const x1 = qToX(prev.year, prev.quarter)
              const x2 = qToX(paper.year, paper.quarter)
              const color = COLORS[paper.paradigm] || '#475569'
              return (
                <line key={`${prev.id}-${paper.id}`}
                  x1={`${x1}%`} y1="40" x2={`${x2}%`} y2="40"
                  stroke={color} strokeWidth="2" strokeOpacity="0.4"
                />
              )
            })}
          </svg>

          {iterPapers.map(paper => {
            const x = qToX(paper.year, paper.quarter)
            const color = COLORS[paper.paradigm] || '#475569'
            const sz = getNodeSize(paper.size) * 1.5
            return (
              <div key={paper.id} className={styles.iterNode} style={{ left: `${x}%` }}>
                <div className={styles.nodeDot} style={{
                  width: sz * 2, height: sz * 2,
                  backgroundColor: `${color}cc`, borderColor: color,
                  borderRadius: LAYER_SHAPES[paper.layer] === 'circle' ? '50%' : '0',
                }} />
                <div className={styles.iterNodeTitle}>{paper.title}</div>
                <div className={styles.iterNodeDate}>{paper.year} Q{paper.quarter}</div>
              </div>
            )
          })}
        </div>

        {/* Mutation cards */}
        <div className={styles.iterCards} style={{ gridTemplateColumns: `repeat(${iterPapers.length}, 1fr)` }}>
          {iterPapers.map(paper => {
            const mutation = iteration.mutations[paper.id]
            const color = COLORS[paper.paradigm] || '#475569'
            if (!mutation) return <div key={paper.id} />
            return (
              <div key={paper.id} className={styles.iterCard} style={{ borderTopColor: color }}>
                <div className={styles.iterCardSummary}>{mutation.summary}</div>
                <div className={styles.iterCardDetail}>{mutation.detail}</div>
                {mutation.bottleneck && (
                  <div className={styles.iterCardSection}>
                    <span className={styles.iterCardLabelRed}>Bottleneck</span>
                    <div className={styles.iterCardText}>{mutation.bottleneck}</div>
                  </div>
                )}
                {mutation.result && (
                  <div className={styles.iterCardSection}>
                    <span className={styles.iterCardLabelGreen}>Result</span>
                    <div className={styles.iterCardText}>{mutation.result}</div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ─── Topic View (Lineage) ───────────────────────────────────────

function TopicView({ laneId, papers, lanes, rows, onBack }: {
  laneId: string
  papers: Paper[]
  lanes: Lane[]
  rows: Row[]
  onBack: () => void
}) {
  const lane = lanes.find(l => l.id === laneId)
  const laneRows = rows.filter(r => r.lane === laneId)
  const lanePapers = papers.filter(p => laneRows.some(r => r.id === p.row))
  const [hovered, setHovered] = useState<string | null>(null)

  const TRACK_H = 55
  const LEFT_MARGIN = 90
  const RIGHT_MARGIN = 20
  const TOP_MARGIN = 40
  const SVG_W = 1200

  const tracks: { row: Row; path: string; index: number }[] = []
  laneRows.forEach(row => {
    const rowPapers = lanePapers.filter(p => p.row === row.id)
    const paths = [...new Set(rowPapers.map(p => p.path))]
    const trunkIdx = paths.indexOf('trunk')
    if (trunkIdx > -1) { paths.splice(trunkIdx, 1); paths.unshift('trunk') }
    paths.forEach(path => {
      tracks.push({ row, path, index: tracks.length })
    })
  })

  const SVG_H = TOP_MARGIN + tracks.length * TRACK_H + 20

  function pos(paperId: string) {
    const paper = lanePapers.find(p => p.id === paperId)
    if (!paper) return null
    const trackIdx = tracks.findIndex(t => t.row.id === paper.row && t.path === paper.path)
    if (trackIdx < 0) return null
    const xPct = qToX(paper.year, paper.quarter) / 100
    return {
      x: LEFT_MARGIN + xPct * (SVG_W - LEFT_MARGIN - RIGHT_MARGIN),
      y: TOP_MARGIN + trackIdx * TRACK_H + TRACK_H / 2,
    }
  }

  const buildsOnEdges = lanePapers
    .filter(p => p.builds_on && p.builds_on.length > 0)
    .flatMap(p => p.builds_on
      .filter(srcId => {
        const src = lanePapers.find(lp => lp.id === srcId)
        return src && src.row === p.row && src.path === p.path
      })
      .map(srcId => ({ from: srcId, to: p.id }))
    )

  const forkEdges = lanePapers
    .filter(p => p.builds_on && p.builds_on.length > 0)
    .flatMap(p => p.builds_on
      .filter(srcId => {
        const src = lanePapers.find(lp => lp.id === srcId)
        return src && (src.row !== p.row || src.path !== p.path)
      })
      .map(srcId => ({ from: srcId, to: p.id }))
    )

  function renderNode(paper: Paper) {
    const p = pos(paper.id)
    if (!p) return null
    const sz = getNodeSize(paper.size)
    const color = COLORS[paper.paradigm] || '#475569'
    const isActive = hovered === paper.id
    const r = sz * (isActive ? 1.3 : 1)
    const fillOpacity = isActive ? 0.8 : 0.5

    let shapeEl: React.ReactNode
    const shape = LAYER_SHAPES[paper.layer] || 'circle'
    if (shape === 'circle') {
      shapeEl = <circle cx={p.x} cy={p.y} r={r} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={isActive ? 2 : 1.5} />
    } else if (shape === 'square') {
      shapeEl = <rect x={p.x - r} y={p.y - r} width={r * 2} height={r * 2} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={isActive ? 2 : 1.5} />
    } else if (shape === 'diamond') {
      shapeEl = <rect x={p.x - r * 0.8} y={p.y - r * 0.8} width={r * 1.6} height={r * 1.6} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={isActive ? 2 : 1.5} transform={`rotate(45 ${p.x} ${p.y})`} />
    } else if (shape === 'triangle') {
      const pts = `${p.x},${p.y - r} ${p.x - r},${p.y + r} ${p.x + r},${p.y + r}`
      shapeEl = <polygon points={pts} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={isActive ? 2 : 1.5} />
    } else {
      const a = r
      const pts = [0,1,2,3,4,5].map(i => {
        const ang = Math.PI / 6 + i * Math.PI / 3
        return `${p.x + a * Math.cos(ang)},${p.y + a * Math.sin(ang)}`
      }).join(' ')
      shapeEl = <polygon points={pts} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={isActive ? 2 : 1.5} />
    }

    return (
      <g key={paper.id} style={{ cursor: 'pointer' }}
        onMouseEnter={() => setHovered(paper.id)}
        onMouseLeave={() => setHovered(null)}>
        {shapeEl}
        <text x={p.x} y={p.y + r + 12} textAnchor="middle" fontSize="9" fill="#52525b" fontFamily="IBM Plex Sans">
          {paper.title}
        </text>
      </g>
    )
  }

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.breadcrumb}>
          <button onClick={onBack} className={styles.backBtn}>← Back</button>
          <span className={styles.breadcrumbSep}>›</span>
          <span style={{ color: lane?.color }}>{lane?.title}</span>
          <span className={styles.breadcrumbSep}>›</span>
          <span className={styles.breadcrumbCurrent}>Lineage</span>
        </div>
      </header>

      <div className={styles.iterContent}>
        <div className={styles.iterTitle}>
          <h2>{lane?.title} — Lineage</h2>
          <p>{lane?.subtitle} · 技术路线谱系树</p>
        </div>

        <svg viewBox={`0 0 ${SVG_W} ${SVG_H}`} style={{ width: '100%', maxHeight: '75vh', marginTop: 24 }}>
          {['2023', '2024', '2025', '2026'].map((yr, i) => {
            const x0 = LEFT_MARGIN + i * (SVG_W - LEFT_MARGIN - RIGHT_MARGIN) / 4
            const x1 = LEFT_MARGIN + (i + 1) * (SVG_W - LEFT_MARGIN - RIGHT_MARGIN) / 4
            return (
              <g key={yr}>
                <line x1={x0} y1={0} x2={x0} y2={SVG_H} stroke="#f4f4f5" strokeWidth="1" />
                <text x={(x0 + x1) / 2} y={14} textAnchor="middle" fontSize="12" fontWeight="700" fill="#3f3f46" fontFamily="IBM Plex Sans">{yr}</text>
                {['Q1','Q2','Q3','Q4'].map((q, qi) => {
                  const qx = x0 + qi * (x1 - x0) / 4 + (x1 - x0) / 8
                  return <text key={q} x={qx} y={28} textAnchor="middle" fontSize="8" fill="#a1a1aa" fontFamily="IBM Plex Sans">{q}</text>
                })}
              </g>
            )
          })}
          <line x1={LEFT_MARGIN} y1={TOP_MARGIN - 5} x2={SVG_W - RIGHT_MARGIN} y2={TOP_MARGIN - 5} stroke="#e4e4e7" strokeWidth="1" />

          {tracks.map(({ row, path, index }) => {
            const y = TOP_MARGIN + index * TRACK_H + TRACK_H / 2
            const isFirstOfRow = index === 0 || tracks[index - 1]?.row.id !== row.id
            return (
              <g key={`track-${row.id}-${path}`}>
                <line x1={LEFT_MARGIN} y1={y} x2={SVG_W - RIGHT_MARGIN} y2={y} stroke="#f4f4f5" strokeWidth="1" strokeDasharray="4 2" />
                <text x={LEFT_MARGIN - 8} y={y + 3} textAnchor="end" fontSize="8" fill="#a1a1aa" fontFamily="IBM Plex Sans">
                  {path === 'trunk' ? '●' : path}
                </text>
                {isFirstOfRow && (
                  <text x={LEFT_MARGIN} y={TOP_MARGIN + index * TRACK_H - 2} fontSize="9" fontWeight="700" fill="#a1a1aa" fontFamily="IBM Plex Sans">
                    {row.title}
                  </text>
                )}
              </g>
            )
          })}

          {buildsOnEdges.map(({ from, to }) => {
            const p1 = pos(from)
            const p2 = pos(to)
            if (!p1 || !p2) return null
            const fromPaper = lanePapers.find(p => p.id === from)
            const color = COLORS[fromPaper?.paradigm || ''] || '#475569'
            const isActive = hovered === from || hovered === to
            return (
              <line key={`bo-${from}-${to}`}
                x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke={color} strokeWidth={isActive ? 2 : 1.5}
                strokeOpacity={isActive ? 0.8 : 0.35}
                markerEnd="url(#topic-arrow)" />
            )
          })}

          {forkEdges.map(({ from, to }) => {
            const p1 = pos(from)
            const p2 = pos(to)
            if (!p1 || !p2) return null
            const fromPaper = lanePapers.find(p => p.id === from)
            const color = COLORS[fromPaper?.paradigm || ''] || '#475569'
            const isActive = hovered === from || hovered === to
            const cp1x = p1.x + (p2.x - p1.x) * 0.3
            const cp2x = p1.x + (p2.x - p1.x) * 0.7
            return (
              <path key={`fork-${from}-${to}`}
                d={`M${p1.x},${p1.y} C${cp1x},${p1.y} ${cp2x},${p2.y} ${p2.x},${p2.y}`}
                fill="none" stroke={color}
                strokeWidth={isActive ? 2 : 1.5}
                strokeOpacity={isActive ? 0.6 : 0.2}
                strokeDasharray="6 3"
                markerEnd="url(#topic-arrow)" />
            )
          })}

          {lanePapers.map(paper => renderNode(paper))}

          <defs>
            <marker id="topic-arrow" markerWidth="6" markerHeight="5" refX="5" refY="2.5" orient="auto">
              <polygon points="0 0,6 2.5,0 5" fill="#a1a1aa" fillOpacity="0.6" />
            </marker>
          </defs>
        </svg>
      </div>
    </div>
  )
}

// ─── Global View ────────────────────────────────────────────────

export default function EvolutionPage() {
  const [data, setData] = useState<MapData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [selected, setSelected] = useState<Paper | null>(null)
  const [currentView, setCurrentView] = useState<{ type: 'global' } | { type: 'iteration'; id: string } | { type: 'topic'; laneId: string }>({ type: 'global' })
  const [hoveredTrack, setHoveredTrack] = useState<string | null>(null)

  useEffect(() => {
    fetch('http://localhost:8000/api/evolution-map')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(setData)
      .catch(e => setError(e.message))
  }, [])

  if (error) return <div className={styles.error}>API Error: {error}</div>
  if (!data) return <div className={styles.loading}>Loading evolution map...</div>

  // Topic (Lineage) view routing
  if (currentView.type === 'topic') {
    return <TopicView laneId={currentView.laneId} papers={data.papers} lanes={data.lanes} rows={data.rows} onBack={() => setCurrentView({ type: 'global' })} />
  }

  // Iteration view routing
  if (currentView.type === 'iteration') {
    const iter = data.iterations.find(i => i.id === currentView.id)
    if (!iter) return <div className={styles.error}>Iteration not found</div>
    return <IterationView iteration={iter} papers={data.papers} lanes={data.lanes} rows={data.rows} onBack={() => setCurrentView({ type: 'global' })} />
  }

  const toggleRow = (rowId: string) => {
    setExpandedRows(prev => {
      const next = new Set(prev)
      if (next.has(rowId)) { next.delete(rowId) } else { next.add(rowId) }
      return next
    })
  }

  const expandAll = () => setExpandedRows(new Set(data.rows.map(r => r.id)))
  const collapseAll = () => setExpandedRows(new Set())

  // Layout computation
  const ROW_HEADER_H = 28
  const TRACK_H = 44
  const COLLAPSED_H = 56
  const TIMELINE_H = 72

  type RowLayout = { top: number; height: number; paths: string[] }
  const rowLayouts: Record<string, RowLayout> = {}
  let currentY = TIMELINE_H

  for (const row of data.rows) {
    const isExpanded = expandedRows.has(row.id)
    const rowPapers = data.papers.filter(p => p.row === row.id)
    const paths = [...new Set(rowPapers.map(p => p.path))]
    const trunkIdx = paths.indexOf('trunk')
    if (trunkIdx > -1) { paths.splice(trunkIdx, 1); paths.unshift('trunk') }
    const height = isExpanded ? ROW_HEADER_H + paths.length * TRACK_H : COLLAPSED_H
    rowLayouts[row.id] = { top: currentY, height, paths }
    currentY += height
  }

  const totalHeight = currentY

  // Lane heights
  const laneHeights: Record<string, number> = {}
  for (const lane of data.lanes) {
    laneHeights[lane.id] = data.rows
      .filter(r => r.lane === lane.id)
      .reduce((sum, r) => sum + rowLayouts[r.id].height, 0)
  }

  // Paper positions
  const paperPos: Record<string, { x: number; y: number }> = {}
  for (const paper of data.papers) {
    const rl = rowLayouts[paper.row]
    if (!rl) continue
    const x = qToX(paper.year, paper.quarter)
    const isExpanded = expandedRows.has(paper.row)
    let y: number
    if (isExpanded) {
      const pathIdx = rl.paths.indexOf(paper.path)
      y = rl.top + ROW_HEADER_H + pathIdx * TRACK_H + TRACK_H / 2
    } else {
      y = rl.top + COLLAPSED_H / 2
    }
    paperPos[paper.id] = { x, y }
  }

  // Find iteration for a given (row, path) combo
  const getIteration = (rowId: string, path: string) =>
    data.iterations.find(i => i.row === rowId && i.path === path)

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>AI Tech Evolution Map</h1>
          <p className={styles.subtitle}>点击行展开技术路径 · hover 轨道查看 Evolution · 点击节点查看详情</p>
        </div>
        <div className={styles.controls}>
          <button onClick={collapseAll} className={styles.btn}>全部折叠</button>
          <button onClick={expandAll} className={styles.btnPrimary}>全部展开</button>
        </div>
      </header>

      <div className={styles.main}>
        <div className={styles.scrollArea}>
          {/* Left rail */}
          <div className={styles.leftRail}>
            <div style={{ height: TIMELINE_H }} />
            {data.lanes.map(lane => (
              <div key={lane.id} className={styles.laneLabel}
                style={{ height: laneHeights[lane.id], borderLeftColor: lane.color, cursor: 'pointer' }}
                onClick={() => setCurrentView({ type: 'topic', laneId: lane.id })}>
                <div className={styles.laneName}>{lane.title}</div>
                <div className={styles.laneSub}>{lane.subtitle}</div>
                <div style={{ fontSize: 9, color: '#a1a1aa', marginTop: 4 }}>View Lineage ↗</div>
              </div>
            ))}
          </div>

          {/* Canvas */}
          <div className={styles.canvas} style={{ height: totalHeight, minWidth: 1000 }}>
            {/* Timeline header */}
            <div className={styles.timeline}>
              {['2023', '2024', '2025', '2026'].map(y => (
                <div key={y} className={styles.yearCol}>
                  <div className={styles.yearLabel}>{y}</div>
                  <div className={styles.quarters}>
                    {['Q1','Q2','Q3','Q4'].map(q => <div key={q} className={styles.qLabel}>{q}</div>)}
                  </div>
                </div>
              ))}
            </div>

            {/* Era labels */}
            <div className={styles.eraRow}>
              <div className={styles.era} style={{ width: '25%', background: '#f8f8f8' }}>Era 1: Knowledge Acquisition</div>
              <div className={styles.era} style={{ width: '31.25%' }}>Era 2: Logical Reasoning</div>
              <div className={styles.era} style={{ width: '43.75%', background: '#fffbeb' }}>Era 3: Unified Action</div>
            </div>

            {/* NOW line */}
            <div className={styles.nowLine} style={{ left: `${qToX(2026, 2)}%`, top: TIMELINE_H }} />
            <div className={styles.nowLabel} style={{ left: `${qToX(2026, 2)}%` }}>NOW</div>

            {/* Rows */}
            {data.rows.map(row => {
              const rl = rowLayouts[row.id]
              const isExpanded = expandedRows.has(row.id)
              const rowPapers = data.papers.filter(p => p.row === row.id)

              return (
                <div key={row.id} className={styles.row} style={{ top: rl.top, height: rl.height }}>
                  <div className={styles.rowHeader} onClick={() => toggleRow(row.id)}>
                    <span className={styles.rowTitle}>{row.title}</span>
                    <span className={styles.rowSub}>{row.subtitle}</span>
                    <span className={styles.rowToggle}>{isExpanded ? '▼' : '▶'}</span>
                  </div>

                  {/* Track hover zones (expanded only) */}
                  {isExpanded && rl.paths.map((path, idx) => {
                    const iter = getIteration(row.id, path)
                    const trackKey = `${row.id}-${path}`
                    const isHovered = hoveredTrack === trackKey
                    return (
                      <div
                        key={path}
                        className={styles.track}
                        style={{ top: ROW_HEADER_H + idx * TRACK_H, height: TRACK_H }}
                        onMouseEnter={() => setHoveredTrack(trackKey)}
                        onMouseLeave={() => setHoveredTrack(null)}
                      >
                        <div className={styles.trackLine} />
                        {iter && isHovered && (
                          <button
                            className={styles.viewEvoBtn}
                            onClick={(e) => { e.stopPropagation(); setCurrentView({ type: 'iteration', id: iter.id }) }}
                          >
                            View Evolution ↗
                          </button>
                        )}
                      </div>
                    )
                  })}

                  {/* Paper nodes */}
                  {rowPapers.map(paper => {
                    const pos = paperPos[paper.id]
                    if (!pos) return null
                    const sz = getNodeSize(paper.size)
                    const color = COLORS[paper.paradigm] || '#475569'
                    const isTrunk = paper.path === 'trunk'
                    const show = isExpanded || isTrunk

                    return (
                      <div
                        key={paper.id}
                        className={styles.node}
                        style={{
                          left: `${pos.x}%`,
                          top: pos.y - rl.top - sz,
                          opacity: show ? 1 : 0.4,
                          zIndex: isTrunk ? 10 : 5,
                        }}
                        onClick={(e) => { e.stopPropagation(); setSelected(paper) }}
                        title={`${paper.title} · ${paper.year} Q${paper.quarter}`}
                      >
                        <div
                          className={styles.nodeDot}
                          style={{
                            width: sz * 2, height: sz * 2,
                            backgroundColor: `${color}cc`,
                            borderColor: color,
                            borderRadius: LAYER_SHAPES[paper.layer] === 'circle' ? '50%' :
                              LAYER_SHAPES[paper.layer] === 'diamond' ? '2px' : '0',
                            transform: LAYER_SHAPES[paper.layer] === 'diamond' ? 'rotate(45deg) scale(0.85)' : undefined,
                          }}
                        />
                        {show && (
                          <div className={styles.nodeLabel}>
                            <div>{paper.title}</div>
                            {isExpanded && <div className={styles.nodeDate}>{paper.year} Q{paper.quarter}</div>}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )
            })}
          </div>
        </div>

        {/* Side panel */}
        {selected && (
          <aside className={styles.panel}>
            <button className={styles.panelClose} onClick={() => setSelected(null)}>×</button>
            <h2 className={styles.panelTitle}>{selected.title}</h2>
            <div className={styles.panelMeta}>{selected.year} Q{selected.quarter}</div>
            <div className={styles.panelField}><span>Paradigm</span><span>{selected.paradigm}</span></div>
            <div className={styles.panelField}><span>Layer</span><span>{selected.layer}</span></div>
            <div className={styles.panelField}><span>Path</span><span>{selected.path}</span></div>
            <div className={styles.panelField}><span>Size</span><span>{selected.size}</span></div>
            {selected.builds_on.length > 0 && (
              <div className={styles.panelField}><span>Builds on</span><span>{selected.builds_on.join(', ')}</span></div>
            )}
          </aside>
        )}
      </div>
    </div>
  )
}
