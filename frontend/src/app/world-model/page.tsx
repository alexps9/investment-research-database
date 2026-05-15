'use client'

import { useState } from 'react'
import worldModelData from '@/data/world-model-data.json'
import styles from '../evolution/page.module.css'

interface Lane { id: string; title: string; subtitle: string; color: string }
interface Row { id: string; lane: string; title: string; subtitle: string }
interface Paper {
  id: string; title: string; year: number; quarter: number
  paradigm: string; layer: string; lane: string; row: string
  path: string; size: string; builds_on: string[]
  impact_score?: number | null
  is_rising?: boolean
  is_weak_signal?: boolean
}
interface Mutation { summary: string; detail: string; bottleneck?: string; result?: string }
interface Iteration {
  id: string; title: string; subtitle: string; path: string; row: string
  papers: string[]
  mutations: Record<string, Mutation>
}
interface MapData { lanes: Lane[]; rows: Row[]; papers: Paper[]; iterations: Iteration[] }

const data = worldModelData as unknown as MapData

// Player colors — max 8, rest is gray
const PLAYER_COLORS: Record<string, string> = {
  'DeepMind': '#4285F4',
  'Meta': '#8B5CF6',
  'OpenAI': '#10A37F',
  'NVIDIA': '#76B900',
  'Physical Intelligence': '#E04E39',
  'UC Berkeley': '#FDB515',
  'Wayve': '#6B21A8',
  'Google Brain': '#4285F4',
}
const OTHER_COLOR = '#9CA3AF'

// Map paper IDs to player/org
const PAPER_PLAYER: Record<string, string> = {
  planet: 'DeepMind', dreamer_v1: 'DeepMind', dreamer_v2: 'DeepMind', dreamer_v3: 'DeepMind',
  dreamsmooth: 'DeepMind', pigdreamer: 'DeepMind', harmonydream: 'DeepMind', dymodreamer: 'DeepMind',
  genie2: 'DeepMind', hieros: 'DeepMind', thick: 'DeepMind',
  sora: 'OpenAI', gpt4: 'OpenAI',
  i_jepa: 'Meta', v_jepa: 'Meta', v_jepa_2: 'Meta', seq_jepa: 'Meta', mc_jepa: 'Meta',
  llama3: 'Meta', dino_wm: 'Meta', dino_world: 'Meta', dino_foresight: 'Meta',
  cosmos: 'NVIDIA', gen3: 'Runway', wan: 'Alibaba', teleworld: 'Tencent',
  tdmpc: 'UC Berkeley', tdmpc2: 'UC Berkeley', pwm: 'UC Berkeley',
  slot_attention: 'Google Brain', slotformer: 'NUS',
  tesseract: 'MIT', llava: 'UW-Madison',
  rt2: 'DeepMind', octo: 'UC Berkeley',
  diffusion_policy: 'Columbia', pi0: 'Physical Intelligence',
  gaia1: 'Wayve', drivevla: 'Wayve', uniworld: 'Wayve',
  diffuser: 'UC Berkeley', decision_diffuser: 'UC Berkeley',
  drive_wm: 'NVIDIA', vista: 'NVIDIA',
  genie_envisioner: 'DeepMind', gamenngen: 'DeepMind',
  copilot4d: 'NVIDIA',
}

function getNodeColor(paperId: string): string {
  const player = PAPER_PLAYER[paperId]
  if (player && PLAYER_COLORS[player]) return PLAYER_COLORS[player]
  return OTHER_COLOR
}

function getPlayerLabel(paperId: string): string {
  return PAPER_PLAYER[paperId] || ''
}

// Track (赛道/application domain) — for filtering
const TRACKS = ['Multimodal Video', 'Autonomous Driving', 'Embodied Robotics', 'Spatial Intelligence', '3D Games/VR'] as const
const PAPER_TRACK: Record<string, string> = {
  sora: 'Multimodal Video', gen3: 'Multimodal Video', wan: 'Multimodal Video', cosmos: 'Multimodal Video',
  emu3: 'Multimodal Video', lwm: 'Multimodal Video', teleworld: 'Multimodal Video',
  ivideogpt: 'Multimodal Video', genie_envisioner: 'Multimodal Video',
  gaia1: 'Autonomous Driving', drivevla: 'Autonomous Driving', uniworld: 'Autonomous Driving',
  drive_wm: 'Autonomous Driving', vista: 'Autonomous Driving', copilot4d: 'Autonomous Driving',
  think2drive: 'Autonomous Driving', x_mobility: 'Autonomous Driving',
  rt2: 'Embodied Robotics', octo: 'Embodied Robotics', pi0: 'Embodied Robotics',
  diffusion_policy: 'Embodied Robotics', tesseract: 'Embodied Robotics',
  planet: 'Embodied Robotics', dreamer_v1: 'Embodied Robotics', dreamer_v2: 'Embodied Robotics', dreamer_v3: 'Embodied Robotics',
  tdmpc: 'Embodied Robotics', tdmpc2: 'Embodied Robotics', pwm: 'Embodied Robotics',
  robodreamer: 'Embodied Robotics', flowdreamer: 'Embodied Robotics',
  diffuser: 'Embodied Robotics', decision_diffuser: 'Embodied Robotics', pivot_r: 'Embodied Robotics',
  navmorph: 'Embodied Robotics',
  i_jepa: 'Spatial Intelligence', v_jepa: 'Spatial Intelligence', v_jepa_2: 'Spatial Intelligence',
  seq_jepa: 'Spatial Intelligence', mc_jepa: 'Spatial Intelligence',
  dino_wm: 'Spatial Intelligence', dino_world: 'Spatial Intelligence', dino_foresight: 'Spatial Intelligence',
  text2room: 'Spatial Intelligence', wonderworld: 'Spatial Intelligence', falconwing: 'Spatial Intelligence',
  slot_attention: 'Spatial Intelligence', slotformer: 'Spatial Intelligence',
  genie2: '3D Games/VR', oasis: '3D Games/VR', gamenngen: '3D Games/VR',
}

const PATH_LABELS: Record<string, string> = {
  'diffusion_video:trunk': 'Sora / Wan',
  'diffusion_video:embodied': 'Embodied Sim',
  'diffusion_video:game': 'Interactive',
  'rssm_based:trunk': 'Dreamer',
  'rssm_based:robotics': 'Robotics',
  'rssm_based:extensions': 'Extensions',
  'slot_based:trunk': 'SlotFormer',
  'slot_based:applications': 'Applications',
}

const LAYER_SHAPES: Record<string, string> = {
  arch: 'circle', sys: 'square', infer: 'diamond', train: 'triangle', memory: 'hexagon',
}

const START_YEAR = 2020
const END_YEAR = 2027
const NUM_YEARS = END_YEAR - START_YEAR

function getNodeRadius(paper: Paper): number {
  const MIN_R = 4, MAX_R = 16
  if (paper.impact_score != null) {
    return MIN_R + (MAX_R - MIN_R) * Math.pow(paper.impact_score / 100, 0.6)
  }
  return paper.size === 'lg' ? 10 : paper.size === 'md' ? 7 : 5
}

function yearRange(): number[] {
  const years: number[] = []
  for (let y = START_YEAR; y < END_YEAR; y++) years.push(y)
  return years
}

function qToXDynamic(year: number, quarter: number, yearWidths: number[]): number {
  const yearIdx = year - START_YEAR
  let x = 0
  for (let i = 0; i < Math.min(yearIdx, NUM_YEARS); i++) x += yearWidths[i]
  if (yearIdx >= 0 && yearIdx < NUM_YEARS) {
    x += yearWidths[yearIdx] * ((quarter - 1) / 4)
  }
  return x
}

const DEFAULT_YEAR_WIDTHS = new Array(NUM_YEARS).fill(100 / NUM_YEARS)

function qToX(year: number, quarter: number): number {
  return qToXDynamic(year, quarter, DEFAULT_YEAR_WIDTHS)
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
  const years = yearRange()
  const NUM_YEARS = years.length

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
    const sz = getNodeRadius(paper)
    const color = getNodeColor(paper.id)
    const isActive = hovered === paper.id
    const r = sz * (isActive ? 1.3 : 1)
    const fillOpacity = isActive ? 0.8 : 0.5

    const sw = isActive ? 2 : 1.5
    const dash = paper.is_weak_signal ? "3,2" : undefined
    let shapeEl: React.ReactNode
    const shape = LAYER_SHAPES[paper.layer] || 'circle'
    if (shape === 'circle') {
      shapeEl = <circle cx={p.x} cy={p.y} r={r} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={sw} strokeDasharray={dash} />
    } else if (shape === 'square') {
      shapeEl = <rect x={p.x - r} y={p.y - r} width={r * 2} height={r * 2} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={sw} strokeDasharray={dash} />
    } else if (shape === 'diamond') {
      shapeEl = <rect x={p.x - r * 0.8} y={p.y - r * 0.8} width={r * 1.6} height={r * 1.6} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={sw} strokeDasharray={dash} transform={`rotate(45 ${p.x} ${p.y})`} />
    } else if (shape === 'triangle') {
      const pts = `${p.x},${p.y - r} ${p.x - r},${p.y + r} ${p.x + r},${p.y + r}`
      shapeEl = <polygon points={pts} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={sw} strokeDasharray={dash} />
    } else {
      const a = r
      const pts = [0,1,2,3,4,5].map(i => {
        const ang = Math.PI / 6 + i * Math.PI / 3
        return `${p.x + a * Math.cos(ang)},${p.y + a * Math.sin(ang)}`
      }).join(' ')
      shapeEl = <polygon points={pts} fill={color} fillOpacity={fillOpacity} stroke={color} strokeWidth={sw} strokeDasharray={dash} />
    }

    const glowEl = paper.is_rising ? (
      <circle cx={p.x} cy={p.y} r={r + 4} fill="none" stroke={color} strokeWidth={2} opacity={0.3} filter="url(#rising-glow)" />
    ) : null

    return (
      <g key={paper.id} style={{ cursor: 'pointer' }}
        onMouseEnter={() => setHovered(paper.id)}
        onMouseLeave={() => setHovered(null)}>
        {glowEl}
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
          {years.map((yr, i) => {
            const x0 = LEFT_MARGIN + i * (SVG_W - LEFT_MARGIN - RIGHT_MARGIN) / NUM_YEARS
            const x1 = LEFT_MARGIN + (i + 1) * (SVG_W - LEFT_MARGIN - RIGHT_MARGIN) / NUM_YEARS
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
            const color = getNodeColor(fromPaper?.id || '')
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
            const color = getNodeColor(fromPaper?.id || '')
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
            <filter id="rising-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>
        </svg>
      </div>
    </div>
  )
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

        <div className={styles.iterTimeline}>
          {yearRange().map(y => (
            <div key={y} className={styles.iterYear}>
              <div className={styles.iterYearLabel}>{y}</div>
              <div className={styles.iterQuarters}>
                {['Q1','Q2','Q3','Q4'].map(q => <span key={q}>{q}</span>)}
              </div>
            </div>
          ))}
        </div>

        <div className={styles.iterNodes}>
          <svg className={styles.iterSvg}>
            {iterPapers.map((paper, i) => {
              if (i === 0) return null
              const prev = iterPapers[i - 1]
              const x1 = qToX(prev.year, prev.quarter)
              const x2 = qToX(paper.year, paper.quarter)
              const color = getNodeColor(paper.id)
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
            const color = getNodeColor(paper.id)
            const sz = getNodeRadius(paper) * 1.5
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

        <div className={styles.iterCards} style={{ gridTemplateColumns: `repeat(${iterPapers.length}, 1fr)` }}>
          {iterPapers.map(paper => {
            const mutation = iteration.mutations[paper.id]
            const color = getNodeColor(paper.id)
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

// ─── Global View ────────────────────────────────────────────────

export default function WorldModelPage() {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set(data.rows.map(r => r.id)))
  const [selected, setSelected] = useState<Paper | null>(null)
  const [currentView, setCurrentView] = useState<{ type: 'global' } | { type: 'iteration'; id: string } | { type: 'topic'; laneId: string }>({ type: 'global' })
  const [hoveredTrack, setHoveredTrack] = useState<string | null>(null)
  const [highlightTrack, setHighlightTrack] = useState<string | null>(null)
  const [filterOpen, setFilterOpen] = useState(false)
  const [yearWidths, setYearWidths] = useState<number[]>(DEFAULT_YEAR_WIDTHS)
  const [dragging, setDragging] = useState<{ idx: number; startX: number; startWidths: number[] } | null>(null)
  const canvasRef = { current: null as HTMLDivElement | null }

  const toX = (year: number, quarter: number) => qToXDynamic(year, quarter, yearWidths)

  const handleDividerDown = (e: React.MouseEvent, idx: number) => {
    e.preventDefault()
    setDragging({ idx, startX: e.clientX, startWidths: [...yearWidths] })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging || !canvasRef.current) return
    const canvasW = canvasRef.current.getBoundingClientRect().width
    const dx = e.clientX - dragging.startX
    const dPct = (dx / canvasW) * 100
    const sw = dragging.startWidths
    const idx = dragging.idx
    const leftSum = sw.slice(0, idx + 1).reduce((a, b) => a + b, 0)
    const rightSum = sw.slice(idx + 1).reduce((a, b) => a + b, 0)
    const newLeftSum = leftSum + dPct
    const newRightSum = rightSum - dPct
    const minPerYear = 2
    const leftCount = idx + 1
    const rightCount = NUM_YEARS - leftCount
    if (newLeftSum < minPerYear * leftCount || newRightSum < minPerYear * rightCount) return
    const leftScale = newLeftSum / leftSum
    const rightScale = newRightSum / rightSum
    const newWidths = sw.map((w, i) => i <= idx ? w * leftScale : w * rightScale)
    setYearWidths(newWidths)
  }

  const handleMouseUp = () => { setDragging(null) }

  if (currentView.type === 'topic') {
    return <TopicView laneId={currentView.laneId} papers={data.papers} lanes={data.lanes} rows={data.rows} onBack={() => setCurrentView({ type: 'global' })} />
  }

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

  const laneHeights: Record<string, number> = {}
  for (const lane of data.lanes) {
    laneHeights[lane.id] = data.rows
      .filter(r => r.lane === lane.id)
      .reduce((sum, r) => sum + rowLayouts[r.id].height, 0)
  }

  const paperPos: Record<string, { x: number; y: number }> = {}
  for (const paper of data.papers) {
    const rl = rowLayouts[paper.row]
    if (!rl) continue
    const x = toX(paper.year, paper.quarter)
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

  const getIteration = (rowId: string, path: string) =>
    data.iterations.find(i => i.row === rowId && i.path === path)

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>World Model Evolution Map</h1>
          <p className={styles.subtitle}>位置 = 建模方式(Lane) × 时间 · 点击节点查看详情</p>
        </div>
        <div className={styles.controls}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginRight: 16, flexWrap: 'wrap' }}>
            {Object.entries(PLAYER_COLORS).filter(([k]) => k !== 'Google Brain').map(([name, color]) => (
              <span key={name} style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 10, fontFamily: 'IBM Plex Sans', color: '#3f3f46' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: color, display: 'inline-block' }} />
                {name}
              </span>
            ))}
            <span style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 10, fontFamily: 'IBM Plex Sans', color: '#a1a1aa' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: OTHER_COLOR, display: 'inline-block' }} />
              Other
            </span>
          </div>
          <button onClick={collapseAll} className={styles.btn}>全部折叠</button>
          <button onClick={expandAll} className={styles.btnPrimary}>全部展开</button>
        </div>
      </header>

      <div className={styles.main}>
        <div className={styles.scrollArea}>
          <div className={styles.leftRail}>
            <div style={{ height: TIMELINE_H }} />
            {data.lanes.map(lane => (
              <div key={lane.id} className={styles.laneLabel}
                style={{ height: laneHeights[lane.id], borderLeftColor: '#E4E4E7', cursor: 'pointer' }}
                onClick={() => setCurrentView({ type: 'topic', laneId: lane.id })}>
                <div className={styles.laneName}>{lane.title}</div>
                <div className={styles.laneSub}>{lane.subtitle}</div>
                <div style={{ fontSize: 9, color: '#a1a1aa', marginTop: 4 }}>View Lineage ↗</div>
              </div>
            ))}
          </div>

          <div
            className={styles.canvas}
            style={{ height: totalHeight, minWidth: 900, cursor: dragging ? 'col-resize' : undefined }}
            ref={el => { canvasRef.current = el }}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            <div className={styles.timeline} style={{ display: 'flex' }}>
              {yearRange().map((y, i) => (
                <div key={y} className={styles.yearCol} style={{ width: `${yearWidths[i]}%`, flex: 'none', position: 'relative' }}>
                  <div className={styles.yearLabel}>{y}</div>
                  <div className={styles.quarters}>
                    {['Q1','Q2','Q3','Q4'].map(q => <div key={q} className={styles.qLabel}>{q}</div>)}
                  </div>
                  {i < NUM_YEARS - 1 && (
                    <div
                      onMouseDown={(e) => handleDividerDown(e, i)}
                      style={{
                        position: 'absolute', right: -3, top: 0, width: 6, height: '100%',
                        cursor: 'col-resize', zIndex: 30,
                      }}
                    >
                      <div style={{ position: 'absolute', left: 2, top: 4, bottom: 4, width: 2, borderRadius: 1, background: dragging?.idx === i ? '#2563EB' : '#d4d4d8', transition: 'background 0.15s' }} />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Event anchors — 从数据倒推，不预设时代 */}
            <div className={styles.eraRow}>
              <div className={styles.era} style={{ width: `${yearWidths.slice(0, 4).reduce((a, b) => a + b, 0)}%`, background: '#f8f8f8' }}>Dreamer/PlaNet 主导期 (2019–2023)</div>
              <div className={styles.era} style={{ width: `${yearWidths.slice(4, 6).reduce((a, b) => a + b, 0)}%` }}>Sora + VLA 爆发 (2024–2025)</div>
              <div className={styles.era} style={{ width: `${yearWidths.slice(6).reduce((a, b) => a + b, 0)}%`, background: '#fffbeb' }}>产业化收敛 (2026+)</div>
            </div>

            {/* NOW line */}
            <div className={styles.nowLine} style={{ left: `${toX(2026, 2)}%`, top: TIMELINE_H }} />
            <div className={styles.nowLabel} style={{ left: `${toX(2026, 2)}%` }}>NOW</div>

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

                  {isExpanded && rl.paths.map((path, idx) => {
                    const iter = getIteration(row.id, path)
                    const trackKey = `${row.id}-${path}`
                    const isHovered = hoveredTrack === trackKey
                    const multiPath = rl.paths.length > 1
                    const pathLabel = multiPath ? PATH_LABELS[`${row.id}:${path}`] || path : ''
                    return (
                      <div
                        key={path}
                        className={styles.track}
                        style={{ top: ROW_HEADER_H + idx * TRACK_H, height: TRACK_H }}
                        onMouseEnter={() => setHoveredTrack(trackKey)}
                        onMouseLeave={() => setHoveredTrack(null)}
                      >
                        <div className={styles.trackLine} />
                        {pathLabel && <span style={{
                          position: 'absolute', left: 4, top: '50%', transform: 'translateY(-50%)',
                          fontSize: 9, color: '#a1a1aa', fontFamily: 'IBM Plex Sans', whiteSpace: 'nowrap',
                        }}>{pathLabel}</span>}
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

                  {rowPapers.map(paper => {
                    const pos = paperPos[paper.id]
                    if (!pos) return null
                    const sz = getNodeRadius(paper)
                    const color = getNodeColor(paper.id)
                    const isTrunk = paper.path === 'trunk'
                    const show = isExpanded || isTrunk
                    const trackMatch = !highlightTrack || PAPER_TRACK[paper.id] === highlightTrack
                    const nodeOpacity = highlightTrack ? (trackMatch ? 1 : 0.15) : (show ? 1 : 0.4)

                    return (
                      <div
                        key={paper.id}
                        className={styles.node}
                        style={{
                          left: `${pos.x}%`,
                          top: pos.y - rl.top - sz,
                          opacity: nodeOpacity,
                          zIndex: trackMatch && highlightTrack ? 20 : (isTrunk ? 10 : 5),
                          transition: 'opacity 0.2s',
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
                            boxShadow: paper.is_rising ? `0 0 ${sz}px ${color}` :
                              (trackMatch && highlightTrack ? `0 0 8px ${color}` : undefined),
                            borderWidth: trackMatch && highlightTrack ? 2.5 : undefined,
                            borderStyle: paper.is_weak_signal ? 'dashed' : undefined,
                          }}
                        />
                        {show && (!highlightTrack || trackMatch) && (paper.impact_score == null ? paper.size !== 'sm' : paper.impact_score > 30) && (
                          <div className={styles.nodeLabel} style={{ maxWidth: 90 }}>
                            <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{paper.title}</div>
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

        {/* Collapsible Track Filter — floats over canvas */}
        <div style={{
          position: 'absolute', top: 80, right: 16, zIndex: 100,
          background: '#fff', borderRadius: 6, border: '1px solid #e4e4e7',
          fontFamily: 'IBM Plex Sans', transition: 'width 0.2s, opacity 0.2s',
          width: filterOpen ? 160 : 'auto',
          overflow: 'hidden',
        }}>
          <button
            onClick={() => setFilterOpen(!filterOpen)}
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              fontSize: 11, fontWeight: 600, color: highlightTrack ? '#2563EB' : '#3f3f46',
              padding: '6px 10px', border: 'none', background: 'transparent',
              cursor: 'pointer', width: '100%', textAlign: 'left',
            }}
          >
            {filterOpen ? '▾' : '▸'} Track {highlightTrack ? `· ${highlightTrack}` : ''}
          </button>
          {filterOpen && (
            <div style={{ padding: '0 6px 8px', display: 'flex', flexDirection: 'column', gap: 2 }}>
              <button
                onClick={() => { setHighlightTrack(null) }}
                style={{
                  fontSize: 11, textAlign: 'left', padding: '3px 6px',
                  border: 'none', borderRadius: 3, cursor: 'pointer',
                  background: !highlightTrack ? '#f4f4f5' : 'transparent',
                  fontWeight: !highlightTrack ? 700 : 400, color: '#3f3f46',
                }}
              >All</button>
              {TRACKS.map(track => (
                <button
                  key={track}
                  onClick={() => setHighlightTrack(highlightTrack === track ? null : track)}
                  style={{
                    fontSize: 11, textAlign: 'left', padding: '3px 6px',
                    border: 'none', borderRadius: 3, cursor: 'pointer',
                    background: highlightTrack === track ? '#f4f4f5' : 'transparent',
                    fontWeight: highlightTrack === track ? 700 : 400, color: '#3f3f46',
                  }}
                >{track}</button>
              ))}
            </div>
          )}
        </div>

        {/* Selected Paper Detail Panel */}
        {selected && (
          <aside className={styles.panel}>
            <button className={styles.panelClose} onClick={() => setSelected(null)}>×</button>
            <h2 className={styles.panelTitle}>{selected.title}</h2>
            {getPlayerLabel(selected.id) && <div style={{ fontSize: 11, color: '#71717a', marginBottom: 4 }}>{getPlayerLabel(selected.id)}</div>}
            <div className={styles.panelMeta}>{selected.year} Q{selected.quarter}</div>
            <div className={styles.panelField}><span>Lane</span><span>{{video_gen:'Video-Generative',latent_space:'Latent-Space',rl_based:'RL-Based',vla:'VLA'}[selected.lane] || '—'}</span></div>
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
