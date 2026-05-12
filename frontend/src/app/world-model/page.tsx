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
}
interface Mutation { summary: string; detail: string; bottleneck?: string; result?: string }
interface Iteration {
  id: string; title: string; subtitle: string; path: string; row: string
  papers: string[]
  mutations: Record<string, Mutation>
}
interface MapData { lanes: Lane[]; rows: Row[]; papers: Paper[]; iterations: Iteration[] }

const data = worldModelData as unknown as MapData

// Application domain colors — 6 tracks, investor-first encoding
const APPLICATION_COLORS: Record<string, string> = {
  video_gen: '#2563EB',
  autonomous_driving: '#EA580C',
  robotics: '#059669',
  spatial: '#7C3AED',
  game_vr: '#DC2626',
  drone: '#475569',
}

// Map paper IDs to application domain (primary use case)
const PAPER_APPLICATION: Record<string, string> = {
  // Lane A: RL-Based — mostly robotics
  planet: 'robotics', dreamer_v1: 'robotics', dreamer_v2: 'robotics', dreamer_v3: 'robotics',
  dreamsmooth: 'robotics', pigdreamer: 'robotics', harmonydream: 'robotics', dymodreamer: 'robotics',
  tdmpc: 'robotics', tdmpc2: 'robotics', pwm: 'robotics', iq_mpc: 'robotics',
  hieros: 'robotics', thick: 'robotics',
  dima: 'robotics', coworld: 'robotics',
  r2i: 'robotics', leq: 'robotics', pcm: 'robotics', waker: 'robotics',
  rem: 'robotics', crssm: 'robotics', adaptive_wm: 'robotics', mosim: 'robotics',
  // Lane B: Observation-Level Generative
  gpt4: 'video_gen', llama3: 'video_gen',
  llmcwm: 'spatial', rap: 'spatial', bytesized32: 'game_vr',
  sora: 'video_gen', gen3: 'video_gen', wan: 'video_gen', cosmos: 'video_gen',
  t2v_turbo: 'video_gen', spmem: 'video_gen', videocrafter2: 'video_gen',
  emu3: 'video_gen', llava: 'video_gen',
  genie2: 'game_vr', oasis: 'game_vr',
  teleworld: 'video_gen', vid2world: 'video_gen', cola_world: 'video_gen',
  text2room: 'spatial', '4dfy': 'spatial', wonderjourney: 'spatial',
  scenescape: 'spatial', wonderworld: 'spatial',
  lidar_crafter: 'autonomous_driving', invisible_stitch: 'spatial',
  // Lane C: Latent-Space
  i_jepa: 'spatial', v_jepa: 'spatial', v_jepa_2: 'robotics',
  seq_jepa: 'spatial', mc_jepa: 'spatial',
  dino_wm: 'robotics', dino_world: 'robotics', dino_foresight: 'robotics',
  world_models_group_latents: 'spatial', lwm: 'video_gen',
  // Lane D: Object-Centric
  slot_attention: 'spatial', slotformer: 'spatial',
  lslotformer: 'robotics', mead: 'robotics',
  dyn_o: 'spatial', g_swm: 'spatial',
  carformer: 'autonomous_driving', focus: 'robotics',
  fioc_wm: 'robotics', objects_matter: 'robotics',
  owm_meets_policy: 'robotics', oc_latent_action: 'robotics',
  compositional_ocl: 'spatial', oc_repr_generalize: 'spatial',
  // Former Lane E → redistributed to A & B
  robodreamer: 'robotics', vipra: 'robotics', flowdreamer: 'robotics',
  grounding_video: 'robotics', tesseract: 'robotics', orv: 'robotics',
  wristworld: 'robotics', irasim: 'robotics', wisa: 'robotics',
}

// Map paper IDs to player/org (used for labels and filter)
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
}

function getNodeColor(paperId: string): string {
  const app = PAPER_APPLICATION[paperId]
  if (app) return APPLICATION_COLORS[app]
  return '#6B7280'
}

function getPlayerLabel(paperId: string): string {
  return PAPER_PLAYER[paperId] || ''
}


const LAYER_SHAPES: Record<string, string> = {
  arch: 'circle', sys: 'square', infer: 'diamond', train: 'triangle', memory: 'hexagon',
}

const START_YEAR = 2020
const END_YEAR = 2027
const TOTAL_QUARTERS = (END_YEAR - START_YEAR) * 4

function qToX(year: number, quarter: number): number {
  return ((year - START_YEAR) * 4 + (quarter - 1)) / TOTAL_QUARTERS * 100
}

function getNodeSize(size: string): number {
  return size === 'lg' ? 10 : size === 'md' ? 7 : 5
}

function yearRange(): string[] {
  const years: string[] = []
  for (let y = START_YEAR; y < END_YEAR; y++) years.push(String(y))
  return years
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
    const sz = getNodeSize(paper.size)
    const color = getNodeColor(paper.id)
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
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [selected, setSelected] = useState<Paper | null>(null)
  const [currentView, setCurrentView] = useState<{ type: 'global' } | { type: 'iteration'; id: string } | { type: 'topic'; laneId: string }>({ type: 'global' })
  const [hoveredTrack, setHoveredTrack] = useState<string | null>(null)
  const [highlightPlayer, setHighlightPlayer] = useState<string | null>(null)
  const [filterOpen, setFilterOpen] = useState(false)

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

  const getIteration = (rowId: string, path: string) =>
    data.iterations.find(i => i.row === rowId && i.path === path)

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>World Model Evolution Map</h1>
          <p className={styles.subtitle}>颜色 = 赛道 · 位置 = 技术范式 × 时间 · 点击节点查看详情</p>
        </div>
        <div className={styles.controls}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginRight: 16 }}>
            {Object.entries(APPLICATION_COLORS).map(([id, color]) => (
              <span key={id} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, fontFamily: 'IBM Plex Sans', color: '#3f3f46' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: color, display: 'inline-block' }} />
                {{video_gen:'视频生成',autonomous_driving:'自动驾驶',robotics:'机器人',spatial:'空间智能',game_vr:'游戏/VR',drone:'无人机'}[id]}
              </span>
            ))}
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

          <div className={styles.canvas} style={{ height: totalHeight, minWidth: 1200 }}>
            <div className={styles.timeline}>
              {yearRange().map(y => (
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
              <div className={styles.era} style={{ width: `${(3*4)/TOTAL_QUARTERS*100}%`, background: '#f8f8f8' }}>Era 1: 潜动力学 (2020–2023)</div>
              <div className={styles.era} style={{ width: `${(2*4)/TOTAL_QUARTERS*100}%` }}>Era 2: 生成式仿真 (2024–2025)</div>
              <div className={styles.era} style={{ width: `${(2*4)/TOTAL_QUARTERS*100}%`, background: '#fffbeb' }}>Era 3: 因果推理 (2026+)</div>
            </div>

            {/* NOW line */}
            <div className={styles.nowLine} style={{ left: `${qToX(2026, 2)}%`, top: TIMELINE_H }} />
            <div className={styles.nowLabel} style={{ left: `${qToX(2026, 2)}%` }}>NOW</div>

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

                  {rowPapers.map(paper => {
                    const pos = paperPos[paper.id]
                    if (!pos) return null
                    const sz = getNodeSize(paper.size)
                    const color = getNodeColor(paper.id)
                    const isTrunk = paper.path === 'trunk'
                    const show = isExpanded || isTrunk
                    const playerMatch = !highlightPlayer || PAPER_PLAYER[paper.id] === highlightPlayer
                    const nodeOpacity = highlightPlayer ? (playerMatch ? 1 : 0.15) : (show ? 1 : 0.4)

                    return (
                      <div
                        key={paper.id}
                        className={styles.node}
                        style={{
                          left: `${pos.x}%`,
                          top: pos.y - rl.top - sz,
                          opacity: nodeOpacity,
                          zIndex: playerMatch && highlightPlayer ? 20 : (isTrunk ? 10 : 5),
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
                            boxShadow: playerMatch && highlightPlayer ? `0 0 8px ${color}` : undefined,
                            borderWidth: playerMatch && highlightPlayer ? 2.5 : undefined,
                          }}
                        />
                        {show && (!highlightPlayer || playerMatch) && (
                          <div className={styles.nodeLabel}>
                            <div>{paper.title}{getPlayerLabel(paper.id) ? ` — ${getPlayerLabel(paper.id)}` : ''}</div>
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

        {/* Collapsible Player Filter — floats over canvas */}
        <div style={{
          position: 'absolute', top: 80, right: 16, zIndex: 100,
          background: '#fff', borderRadius: 6, border: '1px solid #e4e4e7',
          fontFamily: 'IBM Plex Sans', transition: 'width 0.2s, opacity 0.2s',
          width: filterOpen ? 140 : 'auto',
          overflow: 'hidden',
        }}>
          <button
            onClick={() => setFilterOpen(!filterOpen)}
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              fontSize: 11, fontWeight: 600, color: highlightPlayer ? '#2563EB' : '#3f3f46',
              padding: '6px 10px', border: 'none', background: 'transparent',
              cursor: 'pointer', width: '100%', textAlign: 'left',
            }}
          >
            {filterOpen ? '▾' : '▸'} Player {highlightPlayer ? `· ${highlightPlayer}` : ''}
          </button>
          {filterOpen && (
            <div style={{ padding: '0 6px 8px', display: 'flex', flexDirection: 'column', gap: 2 }}>
              <button
                onClick={() => { setHighlightPlayer(null) }}
                style={{
                  fontSize: 11, textAlign: 'left', padding: '3px 6px',
                  border: 'none', borderRadius: 3, cursor: 'pointer',
                  background: !highlightPlayer ? '#f4f4f5' : 'transparent',
                  fontWeight: !highlightPlayer ? 700 : 400, color: '#3f3f46',
                }}
              >All</button>
              {[...new Set(Object.values(PAPER_PLAYER))].sort().map(player => (
                <button
                  key={player}
                  onClick={() => setHighlightPlayer(highlightPlayer === player ? null : player)}
                  style={{
                    fontSize: 11, textAlign: 'left', padding: '3px 6px',
                    border: 'none', borderRadius: 3, cursor: 'pointer',
                    background: highlightPlayer === player ? '#f4f4f5' : 'transparent',
                    fontWeight: highlightPlayer === player ? 700 : 400, color: '#3f3f46',
                  }}
                >{player}</button>
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
            <div className={styles.panelField}><span>Application</span><span>{{video_gen:'视频生成',autonomous_driving:'自动驾驶',robotics:'机器人',spatial:'空间智能',game_vr:'游戏/VR',drone:'无人机'}[PAPER_APPLICATION[selected.id]] || '—'}</span></div>
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
