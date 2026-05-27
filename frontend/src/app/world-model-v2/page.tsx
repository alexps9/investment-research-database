'use client'

import { useState, useEffect, useMemo } from 'react'
import { fetchWorldModel } from '@/lib/api'

interface Lane { id: string; title: string; subtitle: string; color: string }
interface Row { id: string; lane: string; title: string; subtitle: string }
interface Connection {
  target: string
  type: 'inherits' | 'competes' | 'borrows'
}
interface Paper {
  id: string; title: string; year: number; quarter: number
  lane: string; row: string; path: string
  impact_score?: number | null
  shape?: 'circle' | 'square'
  builds_on: string[]
  connections?: Connection[]
  is_rising?: boolean
  is_weak_signal?: boolean
  cited_by_count?: number
  institution_tier?: number
  org?: string
}
interface MapData { lanes: Lane[]; rows: Row[]; papers: Paper[] }

const EMPTY_DATA: MapData = { lanes: [], rows: [], papers: [] }

const LANE_COLORS: Record<string, string> = {
  video_gen: '#2563EB',
  latent_space: '#7C3AED',
  rl_based: '#059669',
  vla: '#EA580C',
}

const PATH_COLORS: Record<string, string> = {
  'diffusion_video:trunk': '#2563EB',
  'diffusion_video:game': '#F59E0B',
  'diffusion_video:embodied': '#10B981',
  'rssm_based:trunk': '#059669',
  'rssm_based:robotics': '#34D399',
  'rssm_based:extensions': '#065F46',
  'slot_based:trunk': '#7C3AED',
  'slot_based:applications': '#A78BFA',
}

const TOP_ORGS = new Set([
  'OpenAI', 'Google DeepMind', 'Google', 'Google/Danijar', 'Google Brain',
  'NVIDIA', 'Stanford/NVIDIA', 'Meta', 'Physical Intelligence',
])

function isTopOrg(org: string | undefined): boolean {
  return !!org && TOP_ORGS.has(org)
}

function getNodeColor(paper: Paper): string {
  const pathKey = `${paper.row}:${paper.path}`
  return PATH_COLORS[pathKey] || LANE_COLORS[paper.lane] || '#9CA3AF'
}

function computeSignals(papers: Paper[]): Map<string, { is_rising: boolean; is_weak_signal: boolean }> {
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1

  const paperAges: { paper: Paper; ageMonths: number; citRate: number }[] = papers.map(p => {
    const pubMonth = (p.quarter - 1) * 3 + 2
    const ageMonths = Math.max(3, (currentYear - p.year) * 12 + (currentMonth - pubMonth))
    const cited = p.cited_by_count ?? 0
    const citRate = cited / ageMonths
    return { paper: p, ageMonths, citRate }
  })

  const recent = paperAges.filter(x => x.ageMonths <= 12)
  const rates = recent.map(x => x.citRate).sort((a, b) => a - b)
  const thresholdIdx = Math.floor(rates.length * 0.8)
  const risingThreshold = rates[thresholdIdx] ?? Infinity

  const result = new Map<string, { is_rising: boolean; is_weak_signal: boolean }>()
  for (const { paper, ageMonths, citRate } of paperAges) {
    const cited = paper.cited_by_count ?? 0
    const instTier = paper.institution_tier ?? 99

    const is_rising = ageMonths <= 12 && citRate >= risingThreshold && citRate > 0
    const is_weak_signal = instTier <= 2 && cited < 20 && ageMonths <= 6

    // Mutual exclusion: weak_signal takes priority over rising for low-citation papers
    result.set(paper.id, {
      is_rising: is_weak_signal ? false : is_rising,
      is_weak_signal,
    })
  }
  return result
}

function seededRandom(seed: number) {
  let s = seed
  return function () {
    s = (s * 1664525 + 1013904223) & 0xFFFFFFFF
    return (s >>> 0) / 0xFFFFFFFF
  }
}

function hashStr(str: string): number {
  let h = 0
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) - h) + str.charCodeAt(i)
    h |= 0
  }
  return Math.abs(h)
}

function impactToRadius(impact: number | null | undefined, isFoundation: boolean): number {
  const score = impact ?? 20
  const base = 3 + (score / 100) * 11
  return isFoundation ? base + 2 : base
}

const ROW_H_MIN = 120
const ROW_H_BASE = 160
const LEFT_MARGIN = 200
const RIGHT_MARGIN = 80
const TOP_MARGIN = 60
const CONTENT_W = 1400

function getRowHeight(paperCount: number): number {
  if (paperCount <= 6) return ROW_H_MIN
  if (paperCount <= 15) return ROW_H_BASE
  return ROW_H_BASE + (paperCount - 15) * 8
}

function timeToX(year: number, quarter: number, startYear: number, endYear: number): number {
  const t = year + (quarter - 1) * 0.25
  const pct = (t - startYear) / (endYear - startYear)
  return LEFT_MARGIN + pct * (CONTENT_W - LEFT_MARGIN - RIGHT_MARGIN)
}

export default function WorldModelV2() {
  const [hoveredPaper, setHoveredPaper] = useState<Paper | null>(null)
  const [mapData, setMapData] = useState<MapData>(EMPTY_DATA)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null)
  const [timeRange, setTimeRange] = useState<[number, number]>([2019, 2027])
  const [filterLane, setFilterLane] = useState<string | null>(null)
  const [view, setView] = useState<'overview' | 'global' | 'lineage'>('overview')
  const startYear = timeRange[0]
  const endYear = timeRange[1]

  useEffect(() => {
    fetchWorldModel()
      .then(d => { setMapData(d as unknown as MapData); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const lanes = mapData.lanes
  const rows = mapData.rows
  const papers = mapData.papers

  const signals = useMemo(() => computeSignals(papers), [papers])

  const filteredLaneRows = useMemo(() => {
    const filtered = filterLane ? lanes.filter(l => l.id === filterLane) : lanes
    return filtered.map(lane => ({
      lane,
      rows: rows.filter(r => r.lane === lane.id),
    }))
  }, [lanes, rows, filterLane])

  const rowHeightMap = useMemo(() => {
    const map: Record<string, number> = {}
    for (const { rows: laneRowList } of filteredLaneRows) {
      for (const row of laneRowList) {
        const count = papers.filter(p => p.row === row.id && (p.year + (p.quarter - 1) * 0.25) >= startYear && (p.year + (p.quarter - 1) * 0.25) < endYear).length
        map[row.id] = getRowHeight(count)
      }
    }
    return map
  }, [filteredLaneRows, papers, startYear, endYear])

  const SVG_H = TOP_MARGIN + Object.values(rowHeightMap).reduce((s, h) => s + h, 0) + 40

  if (loading) return <div style={{ fontFamily: "'IBM Plex Sans', sans-serif", padding: 40, color: '#71717A' }}>Loading...</div>
  if (error) return <div style={{ fontFamily: "'IBM Plex Sans', sans-serif", padding: 40, color: '#DC2626' }}>Error: {error}</div>

  if (view === 'lineage') {
    return (
      <TrunksView
        papers={papers}
        lanes={lanes}
        onBack={() => setView('overview')}
      />
    )
  }

  if (view === 'overview') {
    return (
      <div style={{ fontFamily: "'IBM Plex Sans', sans-serif", background: '#FFFFFF', height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <ControlBar
          startYear={startYear} endYear={endYear} onTimeChange={setTimeRange}
          filterLane={filterLane} onFilterLane={setFilterLane}
          lanes={lanes}
          onViewLineage={() => setView('lineage')}
          view={view} onViewChange={setView}
        />
        <div style={{ flex: 1, overflow: 'auto' }}>
          <OverviewStrips papers={papers} lanes={filterLane ? lanes.filter(l => l.id === filterLane) : lanes} rows={rows} startYear={startYear} endYear={endYear} onDrill={(laneId) => { setFilterLane(laneId); setView('global') }} onSelectPaper={(p) => { setSelectedPaper(p); setView('global') }} />
        </div>
      </div>
    )
  }

  return (
    <div style={{ fontFamily: "'IBM Plex Sans', sans-serif", background: '#FFFFFF', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <ControlBar
        startYear={startYear} endYear={endYear} onTimeChange={setTimeRange}
        filterLane={filterLane} onFilterLane={setFilterLane}
        lanes={lanes}
        onViewLineage={() => setView('lineage')}
        view={view} onViewChange={setView}
      />
      <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
      <svg viewBox={`0 0 ${CONTENT_W} ${SVG_H}`} style={{ display: 'block', width: '100%', minWidth: 900, height: 'auto' }}>
        <defs>
          <filter id="glow-rising" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="blur-small" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="1.8" />
          </filter>
        </defs>
        <style>{`
          @keyframes pulse-rising {
            0%, 100% { opacity: 0.85; }
            50% { opacity: 0.5; }
          }
          .rising-node { animation: pulse-rising 2s ease-in-out infinite; filter: url(#glow-rising); }
        `}</style>
        <TimeAxis startYear={startYear} endYear={endYear} />
        <EraBand startYear={startYear} endYear={endYear} />
        <LaneRows laneRows={filteredLaneRows} papers={papers} signals={signals} hoveredPaper={hoveredPaper} selectedPaper={selectedPaper} onHover={setHoveredPaper} onSelect={setSelectedPaper} startYear={startYear} endYear={endYear} rowHeightMap={rowHeightMap} />
      </svg>
      {selectedPaper && <SidePanel paper={selectedPaper} papers={papers} signals={signals} onClose={() => setSelectedPaper(null)} />}
      </div>
      {hoveredPaper && !selectedPaper && <Tooltip paper={hoveredPaper} />}
    </div>
  )
}

function ControlBar({ startYear, endYear, onTimeChange, filterLane, onFilterLane, lanes, onViewLineage, view, onViewChange }: {
  startYear: number; endYear: number
  onTimeChange: (range: [number, number]) => void
  filterLane: string | null
  onFilterLane: (lane: string | null) => void
  lanes: Lane[]
  onViewLineage: () => void
  view?: 'overview' | 'global' | 'lineage'
  onViewChange?: (v: 'overview' | 'global' | 'lineage') => void
}) {
  const timePresets = [
    { label: '全部', start: 2019, end: 2027 },
    { label: '2023-2026', start: 2023, end: 2027 },
    { label: '2024-2026', start: 2024, end: 2027 },
    { label: '2025-2026', start: 2025, end: 2027 },
  ]

  return (
    <div style={{ padding: '12px 32px', display: 'flex', alignItems: 'center', gap: 24, borderBottom: '1px solid #E4E4E7', background: '#FFF', flexShrink: 0, position: 'relative', zIndex: 10, flexWrap: 'wrap' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 11, color: '#71717A', fontWeight: 500 }}>时间</span>
        {timePresets.map(p => {
          const isActive = startYear === p.start && endYear === p.end
          return (
            <button key={p.label} type="button"
              onMouseDown={(e) => { e.preventDefault(); onTimeChange([p.start, p.end]) }}
              style={{ padding: '3px 8px', fontSize: 10, border: '1px solid #E4E4E7', cursor: 'pointer', background: isActive ? '#18181B' : '#FFF', color: isActive ? '#FFF' : '#3F3F46' }}
            >{p.label}</button>
          )
        })}
      </div>

      <div style={{ width: 1, height: 20, background: '#E4E4E7' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 11, color: '#71717A', fontWeight: 500 }}>赛道</span>
        <button type="button"
          onMouseDown={(e) => { e.preventDefault(); onFilterLane(null) }}
          style={{ padding: '3px 8px', fontSize: 10, border: '1px solid #E4E4E7', cursor: 'pointer', background: !filterLane ? '#18181B' : '#FFF', color: !filterLane ? '#FFF' : '#3F3F46' }}
        >全部</button>
        {lanes.map(lane => {
          const isActive = filterLane === lane.id
          return (
            <button key={lane.id} type="button"
              onMouseDown={(e) => { e.preventDefault(); onFilterLane(isActive ? null : lane.id) }}
              style={{ padding: '3px 8px', fontSize: 10, border: `1px solid ${lane.color}`, cursor: 'pointer', background: isActive ? lane.color : '#FFF', color: isActive ? '#FFF' : lane.color }}
            >{lane.title}</button>
          )
        })}
      </div>

      <div style={{ width: 1, height: 20, background: '#E4E4E7' }} />

      {onViewChange && <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <button type="button" onClick={() => onViewChange('overview')}
          style={{ padding: '3px 10px', fontSize: 10, border: '1px solid #E4E4E7', cursor: 'pointer', background: view === 'overview' ? '#18181B' : '#FFF', color: view === 'overview' ? '#FFF' : '#3F3F46', fontWeight: 500 }}
        >Overview</button>
        <button type="button" onClick={() => onViewChange('global')}
          style={{ padding: '3px 10px', fontSize: 10, border: '1px solid #E4E4E7', cursor: 'pointer', background: view === 'global' ? '#18181B' : '#FFF', color: view === 'global' ? '#FFF' : '#3F3F46', fontWeight: 500 }}
        >Detail</button>
      </div>}

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button type="button"
          onMouseDown={(e) => { e.preventDefault(); onViewLineage() }}
          style={{ padding: '3px 10px', fontSize: 10, border: '1px solid #E4E4E7', cursor: 'pointer', background: '#FFF', color: '#3F3F46', fontWeight: 500 }}
        >Lineage ↗</button>
        <a href="/world-model-v2/table"
          style={{ padding: '3px 10px', fontSize: 10, border: '1px solid #E4E4E7', background: '#FFF', color: '#3F3F46', fontWeight: 500, textDecoration: 'none' }}
        >Table ↗</a>
      </div>
    </div>
  )
}

function TimeAxis({ startYear, endYear }: { startYear: number; endYear: number }) {
  const years = []
  for (let y = startYear; y < endYear; y++) years.push(y)

  return (
    <g>
      <line x1={LEFT_MARGIN} y1={TOP_MARGIN - 10} x2={CONTENT_W - RIGHT_MARGIN} y2={TOP_MARGIN - 10} stroke="#E4E4E7" strokeWidth={1} />
      {years.map(y => {
        const x = timeToX(y, 1, startYear, endYear)
        return (
          <g key={y}>
            <line x1={x} y1={TOP_MARGIN - 14} x2={x} y2={TOP_MARGIN - 6} stroke="#E4E4E7" strokeWidth={1} />
            <text x={x} y={TOP_MARGIN - 22} textAnchor="middle" fontSize={12} fontWeight={600} fill="#3F3F46">{y}</text>
            {[2, 3, 4].map(q => {
              const qx = timeToX(y, q, startYear, endYear)
              return <line key={q} x1={qx} y1={TOP_MARGIN - 12} x2={qx} y2={TOP_MARGIN - 8} stroke="#E4E4E7" strokeWidth={0.5} />
            })}
          </g>
        )
      })}
    </g>
  )
}

const CONVERGING_LANES = new Set(['video_gen', 'rl_based'])
const APPLICATION_LANES = new Set(['vla'])

const ERAS: { label: string; start: [number, number]; end: [number, number]; bg: string }[] = [
  { label: 'Dreamer/PlaNet 主导期 (2019–2023)', start: [2019, 1], end: [2024, 1], bg: '#F5F5F5' },
  { label: 'Sora 爆发 (2024–2025)', start: [2024, 1], end: [2026, 1], bg: '#FFFFFF' },
  { label: '产业化收敛 (2026+)', start: [2026, 1], end: [2027, 5], bg: '#FFFBEB' },
]

function EraBand({ startYear, endYear }: { startYear: number; endYear: number }) {
  const bandY = 6
  const bandH = 18
  const xMin = LEFT_MARGIN
  const xMax = CONTENT_W - RIGHT_MARGIN
  const visible = ERAS.map(era => {
    const x1raw = timeToX(era.start[0], era.start[1], startYear, endYear)
    const x2raw = timeToX(era.end[0], era.end[1], startYear, endYear)
    const x1 = Math.max(xMin, x1raw)
    const x2 = Math.min(xMax, x2raw)
    return { ...era, x1, x2, w: x2 - x1 }
  }).filter(e => e.w > 8)

  return (
    <g>
      {visible.map(e => (
        <g key={e.label}>
          <rect x={e.x1} y={bandY} width={e.w} height={bandH} fill={e.bg} stroke="#E4E4E7" strokeWidth={0.5} />
          <text x={e.x1 + e.w / 2} y={bandY + bandH / 2 + 4} textAnchor="middle" fontSize={11} fontWeight={500} fill="#3F3F46">
            {e.w > 140 ? e.label : e.label.split(' (')[0]}
          </text>
        </g>
      ))}
    </g>
  )
}

function LaneRows({ laneRows, papers, signals, hoveredPaper, selectedPaper, onHover, onSelect, startYear, endYear, rowHeightMap }: {
  laneRows: { lane: Lane; rows: Row[] }[]
  papers: Paper[]
  signals: Map<string, { is_rising: boolean; is_weak_signal: boolean }>
  hoveredPaper: Paper | null
  selectedPaper: Paper | null
  onHover: (p: Paper | null) => void
  onSelect: (p: Paper) => void
  startYear: number; endYear: number
  rowHeightMap: Record<string, number>
}) {
  let yAccum = TOP_MARGIN
  return (
    <g>
      {laneRows.map(({ lane, rows: laneRowList }, laneIdx) => {
        const laneStartY = yAccum

        const prevLane = laneIdx > 0 ? laneRows[laneIdx - 1].lane : null
        const isConvergingBoundary = prevLane && CONVERGING_LANES.has(prevLane.id) && CONVERGING_LANES.has(lane.id)

        const laneH = laneRowList.reduce((s, r) => s + (rowHeightMap[r.id] || ROW_H_BASE), 0)

        const laneElement = (
          <g key={lane.id}>
            {APPLICATION_LANES.has(lane.id) && (
              <rect
                x={LEFT_MARGIN}
                y={laneStartY - 4}
                width={CONTENT_W - LEFT_MARGIN - RIGHT_MARGIN}
                height={laneH + 8}
                fill="#FFF7ED"
                opacity={0.4}
              />
            )}
            {isConvergingBoundary && (
              <ConvergenceFade y={laneStartY} startYear={startYear} endYear={endYear} />
            )}
            {laneRowList.map((row) => {
              const rowY = yAccum
              const rowH = rowHeightMap[row.id] || ROW_H_BASE
              yAccum += rowH
              const rowPapers = papers.filter(p => p.row === row.id && (p.year + (p.quarter - 1) * 0.25) >= startYear && (p.year + (p.quarter - 1) * 0.25) < endYear)
              return (
                <RowBand
                  key={row.id}
                  row={row}
                  lane={lane}
                  papers={rowPapers}
                  signals={signals}
                  y={rowY}
                  rowH={rowH}
                  hoveredPaper={hoveredPaper}
                  selectedPaper={selectedPaper}
                  allPapers={papers}
                  onHover={onHover}
                  onSelect={onSelect}
                  startYear={startYear}
                  endYear={endYear}
                />
              )
            })}
            <LaneLabel lane={lane} startY={laneStartY} rowCount={laneRowList.length} laneH={laneH} isApplication={APPLICATION_LANES.has(lane.id)} />
          </g>
        )
        return laneElement
      })}
    </g>
  )
}

function ConvergenceFade({ y, startYear, endYear }: { y: number; startYear: number; endYear: number }) {
  const fadeStartX = timeToX(2024, 1, startYear, endYear)
  if (fadeStartX > CONTENT_W - RIGHT_MARGIN) return null
  return (
    <g>
      <line x1={LEFT_MARGIN} y1={y} x2={fadeStartX} y2={y} stroke="#E4E4E7" strokeWidth={1} />
      <line x1={fadeStartX} y1={y} x2={fadeStartX + 60} y2={y} stroke="#E4E4E7" strokeWidth={1} opacity={0.5} />
      <text x={fadeStartX + 8} y={y - 4} fontSize={8} fill="#A1A1AA" fontStyle="italic">convergence →</text>
    </g>
  )
}

const LANE_INSIGHTS: Record<string, string> = {
  video_gen: '规模+真实感，2024 起与 RL 融合为 Video World Model',
  rl_based: '核心 idea（想象训练）正被 Video WM 吸收，独立路线在收窄',
  latent_space: 'JEPA 反向押注：不预测像素，直接预测抽象表示',
  vla: '主流仍是 VLA，但 WAM（联合预测视频+动作）正在出现，可能替代 VLA',
}

function LaneLabel({ lane, startY, laneH, isApplication }: { lane: Lane; startY: number; rowCount: number; laneH: number; isApplication?: boolean }) {
  const centerY = startY + laneH / 2
  const insight = LANE_INSIGHTS[lane.id]
  return (
    <g>
      <line x1={LEFT_MARGIN - 10} y1={startY} x2={LEFT_MARGIN - 10} y2={startY + laneH} stroke={lane.color} strokeWidth={3} strokeDasharray={isApplication ? '6 3' : 'none'} />
      <text x={30} y={centerY - 14} fontSize={16} fontWeight={700} fill={isApplication ? '#71717A' : '#18181B'}>{lane.title}</text>
      {isApplication && <text x={30 + lane.title.length * 10 + 4} y={centerY - 14} fontSize={9} fill="#A1A1AA">策略层</text>}
      <text x={30} y={centerY + 4} fontSize={12} fill="#71717A">{lane.subtitle}</text>
      {insight && (
        <text x={30} y={centerY + 22} fontSize={9} fill="#B45309" fontStyle="italic">{insight}</text>
      )}
    </g>
  )
}

function RowBand({ row, papers, signals, y, rowH, hoveredPaper, selectedPaper, allPapers, onHover, onSelect, startYear, endYear }: {
  row: Row; lane: Lane; papers: Paper[]; y: number; rowH: number
  signals: Map<string, { is_rising: boolean; is_weak_signal: boolean }>
  hoveredPaper: Paper | null
  selectedPaper: Paper | null
  allPapers: Paper[]
  onHover: (p: Paper | null) => void
  onSelect: (p: Paper) => void
  startYear: number; endYear: number
}) {
  const positions = useMemo(() => {
    return computeRowPositions(papers, y, rowH, startYear, endYear)
  }, [papers, y, rowH, startYear, endYear])

  const hoveredFoundationId = hoveredPaper && hoveredPaper.shape !== 'square' && papers.some(p => p.id === hoveredPaper.id) ? hoveredPaper.id : null
  const hoveredConnectedIds = useMemo(() => {
    if (!hoveredFoundationId) return new Set<string>()
    const ids = new Set<string>()
    ids.add(hoveredFoundationId)
    for (const p of papers) {
      const pointsToHovered = p.connections?.some(c => c.target === hoveredFoundationId) || p.builds_on?.includes(hoveredFoundationId)
      if (pointsToHovered) ids.add(p.id)
    }
    const hp = papers.find(p => p.id === hoveredFoundationId)
    if (hp?.connections) {
      for (const c of hp.connections) { ids.add(c.target) }
    }
    if (hp?.builds_on) {
      for (const b of hp.builds_on) { ids.add(b) }
    }
    return ids
  }, [hoveredFoundationId, papers])


  return (
    <g>
      <line x1={LEFT_MARGIN} y1={y} x2={CONTENT_W - RIGHT_MARGIN} y2={y} stroke="#F4F4F5" strokeWidth={1} />
      <text x={LEFT_MARGIN + 4} y={y + 16} fontSize={11} fontWeight={600} fill="#3F3F46">{row.title}</text>
      <text x={LEFT_MARGIN + 4 + row.title.length * 7 + 8} y={y + 16} fontSize={9} fill="#A1A1AA">{row.subtitle}</text>

      {papers.map(paper => {
        const pos = positions[paper.id]
        if (!pos) return null
        const isFoundation = paper.shape !== 'square'
        const r = impactToRadius(paper.impact_score, isFoundation)
        const nodeColor = getNodeColor(paper)
        const isHovered = hoveredPaper?.id === paper.id
        const sig = signals.get(paper.id)
        const isRising = sig?.is_rising ?? false
        const isWeakSignal = sig?.is_weak_signal ?? false
        const className = isRising ? 'rising-node' : ''

        let dimmed = false
        if (hoveredFoundationId && !isHovered) {
          dimmed = !hoveredConnectedIds.has(paper.id)
        }
        const isSelected = selectedPaper?.id === paper.id

        return (
          <g key={paper.id}
            onMouseEnter={() => onHover(paper)}
            onMouseLeave={() => onHover(null)}
            onClick={() => onSelect(paper)}
            style={{ cursor: 'pointer', opacity: dimmed ? 0.12 : 1, transition: 'opacity 0.2s' }}
            className={className}
          >
            {isWeakSignal && (
              <circle
                cx={pos.x} cy={pos.y} r={(isHovered ? r + 2 : r) + 3}
                fill="none"
                stroke="#F59E0B"
                strokeWidth={2}
                opacity={0.8}
              />
            )}
            <circle
              cx={pos.x} cy={pos.y} r={isSelected ? r + 1 : isHovered ? r + 2 : r}
              fill={nodeColor}
              opacity={isFoundation ? 0.85 : (paper.impact_score ?? 20) < 15 ? 0.18 : 0.35}
              stroke={isSelected ? '#18181B' : isHovered ? '#18181B' : 'none'}
              strokeWidth={isSelected ? 2.5 : 1}
              filter={!isFoundation && (paper.impact_score ?? 20) < 20 ? 'url(#blur-small)' : undefined}
            />
            {isFoundation && (
              <>
                <text
                  x={pos.x} y={pos.y + r + 11}
                  textAnchor="middle"
                  fontSize={9}
                  fill={isTopOrg(paper.org) ? '#B45309' : '#18181B'}
                  fontWeight={500}
                >{paper.title}</text>
                {paper.org && (
                  <text
                    x={pos.x} y={pos.y + r + 21}
                    textAnchor="middle"
                    fontSize={8}
                    fill={isTopOrg(paper.org) ? '#B45309' : '#A1A1AA'}
                  >{paper.org}</text>
                )}
              </>
            )}
            {!isFoundation && (paper.impact_score ?? 0) > 35 && (
              <text
                x={pos.x} y={pos.y + r + 10}
                textAnchor="middle"
                fontSize={8}
                fill={isTopOrg(paper.org) ? '#B45309' : '#71717A'}
                fontWeight={400}
              >{paper.title}</text>
            )}
          </g>
        )
      })}
    </g>
  )
}

function computeRowPositions(papers: Paper[], rowY: number, rowH: number, startYear: number, endYear: number): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {}
  const foundations = papers.filter(p => p.shape !== 'square')
  const backgrounds = papers.filter(p => p.shape === 'square')
  const foundationIds = new Set(foundations.map(f => f.id))

  const xMin = LEFT_MARGIN + 10
  const xMax = CONTENT_W - RIGHT_MARGIN - 10
  const qW = (CONTENT_W - LEFT_MARGIN - RIGHT_MARGIN) * 0.25 / (endYear - startYear)

  // Union-find: group foundations by reference chains
  const parent: Record<string, string> = {}
  foundations.forEach(f => { parent[f.id] = f.id })
  function find(x: string): string { return parent[x] === x ? x : (parent[x] = find(parent[x])) }
  function union(a: string, b: string) { parent[find(a)] = find(b) }

  foundations.forEach(f => {
    const refs = [...(f.builds_on || []), ...(f.connections || []).map(c => c.target)]
    refs.forEach(ref => { if (foundationIds.has(ref)) union(f.id, ref) })
  })

  const clusters: Record<string, Paper[]> = {}
  foundations.forEach(f => {
    const root = find(f.id)
    if (!clusters[root]) clusters[root] = []
    clusters[root].push(f)
  })

  // Assign Y bands proportional to cluster size
  const clusterList = Object.values(clusters).sort((a, b) => b.length - a.length)
  const totalNodes = foundations.length || 1
  const usableH = rowH - 20
  let yOff = rowY + 10

  const clusterYBand = new Map<string, { center: number; halfH: number }>()
  clusterList.forEach(cluster => {
    const weight = cluster.length / totalNodes
    const bandH = Math.max(30, usableH * weight)
    const center = yOff + bandH / 2
    cluster.forEach(f => { clusterYBand.set(f.id, { center, halfH: bandH / 2 - 5 }) })
    yOff += bandH
  })

  // Place foundations: X=time+jitter, Y=band+jitter, radial collision
  const placed: { x: number; y: number; r: number }[] = []
  const sortedFoundations = [...foundations].sort((a, b) => (b.impact_score || 0) - (a.impact_score || 0))

  sortedFoundations.forEach(f => {
    const rng = seededRandom(hashStr(f.id + '_pos'))
    const baseX = timeToX(f.year, f.quarter, startYear, endYear)
    let x = baseX + (rng() - 0.5) * qW * 0.8
    const band = clusterYBand.get(f.id)!
    let y = band.center + (rng() - 0.5) * band.halfH * 1.4
    const r = impactToRadius(f.impact_score, true)

    for (let attempt = 0; attempt < 30; attempt++) {
      let worst: { x: number; y: number; r: number } | null = null
      let worstOverlap = 0
      for (const p of placed) {
        const dx = x - p.x
        const dy = y - p.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const minDist = r + p.r + 8
        if (dist < minDist) {
          const overlap = minDist - dist
          if (overlap > worstOverlap) { worstOverlap = overlap; worst = p }
        }
      }
      if (!worst) break
      const dx = x - worst.x
      const dy = y - worst.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      x += (dx / dist) * (worstOverlap + 2)
      y += (dy / dist) * (worstOverlap + 2)
    }
    x = Math.max(xMin, Math.min(xMax, x))
    y = Math.max(rowY + r + 5, Math.min(rowY + rowH - r - 5, y))
    positions[f.id] = { x, y }
    placed.push({ x, y, r })
  })

  // Place adaptations: connected ones near their foundation, unconnected spread evenly
  const connected: Paper[] = []
  const unconnected: Paper[] = []
  backgrounds.forEach(paper => {
    const refs = [...(paper.builds_on || []), ...(paper.connections || []).map(c => c.target)]
    const refFoundation = refs.find(r => foundationIds.has(r) && positions[r])
    if (refFoundation) connected.push(paper)
    else unconnected.push(paper)
  })

  // Place connected adaptations near their foundation
  connected.forEach(paper => {
    const rng = seededRandom(hashStr(paper.id + '_cl'))
    const refs = [...(paper.builds_on || []), ...(paper.connections || []).map(c => c.target)]
    const refFoundation = refs.find(r => foundationIds.has(r) && positions[r])!
    const fPos = positions[refFoundation]
    const r = impactToRadius(paper.impact_score, false)
    const angle = rng() * Math.PI * 2
    const dist = 10 + rng() * 28
    let x = fPos.x + Math.cos(angle) * dist
    let y = fPos.y + Math.sin(angle) * dist

    for (let attempt = 0; attempt < 12; attempt++) {
      let collides = false
      for (const p of placed) {
        const dx = x - p.x
        const dy = y - p.y
        const d = Math.sqrt(dx * dx + dy * dy) || 1
        const minDist = r + p.r + 3
        if (d < minDist) {
          const push = minDist - d + 1
          const a2 = Math.atan2(dy, dx) || (rng() * Math.PI * 2)
          x += Math.cos(a2) * push
          y += Math.sin(a2) * push
          collides = true
          break
        }
      }
      if (!collides) break
    }
    x = Math.max(xMin, Math.min(xMax, x))
    y = Math.max(rowY + 5, Math.min(rowY + rowH - 5, y))
    positions[paper.id] = { x, y }
    placed.push({ x, y, r })
  })

  // Place unconnected adaptations with stratified Y to avoid clustering
  unconnected.forEach((paper, idx) => {
    const rng = seededRandom(hashStr(paper.id + '_cl'))
    const baseX = timeToX(paper.year, paper.quarter, startYear, endYear)
    const r = impactToRadius(paper.impact_score, false)
    let x = baseX + (rng() - 0.5) * qW * 0.6
    const ySlot = (idx + 0.5) / Math.max(unconnected.length, 1)
    let y = rowY + 15 + ySlot * (rowH - 30) + (rng() - 0.5) * 20

    for (let attempt = 0; attempt < 12; attempt++) {
      let collides = false
      for (const p of placed) {
        const dx = x - p.x
        const dy = y - p.y
        const d = Math.sqrt(dx * dx + dy * dy) || 1
        const minDist = r + p.r + 3
        if (d < minDist) {
          const push = minDist - d + 1
          const a2 = Math.atan2(dy, dx) || (rng() * Math.PI * 2)
          x += Math.cos(a2) * push
          y += Math.sin(a2) * push
          collides = true
          break
        }
      }
      if (!collides) break
    }
    x = Math.max(xMin, Math.min(xMax, x))
    y = Math.max(rowY + 5, Math.min(rowY + rowH - 5, y))
    positions[paper.id] = { x, y }
    placed.push({ x, y, r })
  })

  return positions
}

function Tooltip({ paper }: { paper: Paper }) {
  return (
    <div style={{
      position: 'fixed', bottom: 24, left: 24,
      background: '#FFF', border: '1px solid #E4E4E7',
      padding: '12px 16px', fontSize: 12, color: '#3F3F46',
      maxWidth: 300, zIndex: 100,
    }}>
      <div style={{ fontWeight: 600, color: '#18181B', marginBottom: 4 }}>{paper.title}</div>
      <div>{paper.year} Q{paper.quarter} · {paper.lane} · {paper.row}</div>
      <div>Impact: {paper.impact_score ?? 'N/A'}</div>
    </div>
  )
}

const CONNECTION_STYLE: Record<string, { label: string; color: string; bg: string }> = {
  inherits: { label: '继承', color: '#059669', bg: '#ECFDF5' },
  competes: { label: '竞争', color: '#DC2626', bg: '#FEF2F2' },
  borrows: { label: '借鉴', color: '#7C3AED', bg: '#F5F3FF' },
}

function SidePanel({ paper, papers, signals, onClose }: { paper: Paper; papers: Paper[]; signals: Map<string, { is_rising: boolean; is_weak_signal: boolean }>; onClose: () => void }) {
  const connections = paper.connections || []
  const citedBy = papers.filter(p => p.builds_on.includes(paper.id))
  const incomingConnections = papers
    .filter(p => p.connections?.some(c => c.target === paper.id))
    .map(p => ({ paper: p, type: p.connections!.find(c => c.target === paper.id)!.type }))

  return (
    <div style={{
      position: 'absolute', top: 0, right: 0, width: 320, height: '100%',
      background: '#FFF', borderLeft: '1px solid #E4E4E7',
      padding: '20px 24px', fontSize: 12, color: '#3F3F46',
      overflowY: 'auto', zIndex: 50,
    }}>
      <button onClick={onClose} style={{ position: 'absolute', top: 12, right: 16, border: 'none', background: 'none', fontSize: 18, cursor: 'pointer', color: '#71717A' }}>×</button>
      <h3 style={{ fontSize: 16, fontWeight: 600, color: '#18181B', marginBottom: 4 }}>{paper.title}</h3>
      {paper.org && <div style={{ fontSize: 11, color: isTopOrg(paper.org) ? '#B45309' : '#71717A', marginBottom: 8 }}>{paper.org}</div>}
      <div style={{ marginBottom: 16, color: '#71717A' }}>{paper.year} Q{paper.quarter}</div>

      <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '8px 12px', marginBottom: 20 }}>
        <span style={{ color: '#A1A1AA' }}>Lane</span><span>{paper.lane}</span>
        <span style={{ color: '#A1A1AA' }}>Row</span><span>{paper.row}</span>
        <span style={{ color: '#A1A1AA' }}>Path</span><span>{paper.path}</span>
        <span style={{ color: '#A1A1AA' }}>Impact</span><span style={{ fontWeight: 600 }}>{paper.impact_score ?? 'N/A'}</span>
        <span style={{ color: '#A1A1AA' }}>Status</span>
        <span>{signals.get(paper.id)?.is_rising ? '🔥 Rising' : signals.get(paper.id)?.is_weak_signal ? '◌ Weak Signal' : '—'}</span>
      </div>

      {connections.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#71717A', marginBottom: 6 }}>本文 → 引用了</div>
          {connections.map(conn => {
            const target = papers.find(p => p.id === conn.target)
            const style = CONNECTION_STYLE[conn.type]
            return (
              <div key={conn.target} style={{ padding: '4px 0', borderBottom: '1px solid #F4F4F5', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 9, padding: '1px 4px', background: style.bg, color: style.color, fontWeight: 500 }}>{style.label}</span>
                <span style={{ color: '#A1A1AA' }}>→</span>
                <span style={{ fontWeight: 500 }}>{target?.title ?? conn.target}</span>
                {target && <span style={{ color: '#A1A1AA' }}>{target.year} Q{target.quarter}</span>}
              </div>
            )
          })}
        </div>
      )}

      {incomingConnections.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#71717A', marginBottom: 6 }}>← 被以下论文引用 ({incomingConnections.length})</div>
          {incomingConnections.map(({ paper: p, type }) => {
            const style = CONNECTION_STYLE[type]
            return (
              <div key={p.id} style={{ padding: '4px 0', borderBottom: '1px solid #F4F4F5', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontWeight: 500 }}>{p.title}</span>
                <span style={{ fontSize: 9, padding: '1px 4px', background: style.bg, color: style.color, fontWeight: 500 }}>{style.label}</span>
                <span style={{ color: '#A1A1AA' }}>→ 本文</span>
              </div>
            )
          })}
        </div>
      )}

      {citedBy.length > 0 && !incomingConnections.length && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#71717A', marginBottom: 6 }}>CITED BY ({citedBy.length})</div>
          {citedBy.map(p => (
            <div key={p.id} style={{ padding: '4px 0', borderBottom: '1px solid #F4F4F5' }}>
              <span style={{ fontWeight: 500 }}>{p.title}</span>
              <span style={{ color: '#A1A1AA', marginLeft: 8 }}>{p.year} Q{p.quarter}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function OverviewStrips({ papers, lanes, rows, startYear, endYear, onDrill, onSelectPaper }: {
  papers: Paper[]; lanes: Lane[]; rows: Row[]
  startYear: number; endYear: number
  onDrill: (laneId: string) => void
  onSelectPaper: (p: Paper) => void
}) {
  const STRIP_H = 90
  const W = 1400
  const LM = 140
  const RM = 40
  const TM = 40
  const H = TM + lanes.length * STRIP_H + 20

  const lanePositions = useMemo(() => {
    const result: Record<string, Record<string, { x: number; y: number }>> = {}
    lanes.forEach(lane => {
      const laneRows = rows.filter(r => r.lane === lane.id)
      const lanePapers = papers.filter(p => p.lane === lane.id &&
        (p.year + (p.quarter - 1) * 0.25) >= startYear &&
        (p.year + (p.quarter - 1) * 0.25) < endYear)

      const rowHeights: Record<string, number> = {}
      laneRows.forEach(r => {
        const count = lanePapers.filter(p => p.row === r.id).length
        rowHeights[r.id] = getRowHeight(count)
      })
      const totalH = Object.values(rowHeights).reduce((s, h) => s + h, 0) || 1

      let accY = 0
      const allPositions: Record<string, { x: number; y: number }> = {}
      laneRows.forEach(r => {
        const rh = rowHeights[r.id] || ROW_H_MIN
        const rowPapers = lanePapers.filter(p => p.row === r.id)
        if (rowPapers.length > 0) {
          const pos = computeRowPositions(rowPapers, accY, rh, startYear, endYear)
          Object.assign(allPositions, pos)
        }
        accY += rh
      })

      // Normalize Y from [0, totalH] → [0, 1]
      const normalized: Record<string, { x: number; y: number }> = {}
      for (const [id, pos] of Object.entries(allPositions)) {
        normalized[id] = { x: pos.x, y: pos.y / totalH }
      }
      result[lane.id] = normalized
    })
    return result
  }, [papers, lanes, rows, startYear, endYear])

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', width: '100%', minWidth: 900, height: 'auto' }}>
      {/* Time axis */}
      {(() => {
        const years: number[] = []
        for (let y = Math.ceil(startYear); y < endYear; y++) years.push(y)
        return years.map(yr => {
          const x = LM + ((yr - startYear) / (endYear - startYear)) * (W - LM - RM)
          return <g key={yr}>
            <line x1={x} y1={TM - 10} x2={x} y2={H} stroke="#F4F4F5" strokeWidth={1} />
            <text x={x} y={TM - 16} textAnchor="middle" fontSize={11} fontWeight={600} fill="#3F3F46">{yr}</text>
          </g>
        })
      })()}

      {/* Lane strips */}
      {lanes.map((lane, laneIdx) => {
        const stripY = TM + laneIdx * STRIP_H
        const positions = lanePositions[lane.id] || {}
        const lanePapers = papers.filter(p => p.lane === lane.id &&
          (p.year + (p.quarter - 1) * 0.25) >= startYear &&
          (p.year + (p.quarter - 1) * 0.25) < endYear)
        const color = LANE_COLORS[lane.id] || '#9CA3AF'

        return <g key={lane.id} style={{ cursor: 'pointer' }} onClick={() => onDrill(lane.id)}>
          <rect x={0} y={stripY} width={W} height={STRIP_H} fill={color} opacity={0.015} />
          <line x1={LM} y1={stripY + STRIP_H} x2={W - RM} y2={stripY + STRIP_H} stroke="#E4E4E7" strokeWidth={0.5} />
          <text x={12} y={stripY + 20} fontSize={12} fontWeight={700} fill={color}>{lane.title}</text>
          <text x={12} y={stripY + 34} fontSize={9} fill="#71717A">{lane.subtitle}</text>
          <text x={12} y={stripY + 50} fontSize={9} fill="#A1A1AA">{lanePapers.length} papers</text>

          {lanePapers.map(paper => {
            const pos = positions[paper.id]
            if (!pos) return null
            const x = pos.x
            const y = stripY + 5 + pos.y * (STRIP_H - 10)

            const impact = paper.impact_score ?? 20
            const r = impact >= 70 ? 5 : impact >= 50 ? 3.5 : 2
            const op = impact >= 70 ? 0.75 : impact >= 50 ? 0.45 : 0.2
            const isFoundation = paper.shape !== 'square'

            return <circle key={paper.id} cx={x} cy={y} r={r} fill={color} opacity={op}
              style={isFoundation ? { cursor: 'pointer' } : undefined}
              onClick={isFoundation ? (e) => { e.stopPropagation(); onSelectPaper(paper) } : undefined}
            />
          })}
        </g>
      })}
    </svg>
  )
}

function TrunksView({ papers, lanes, onBack }: {
  papers: Paper[]; lanes: Lane[]; onBack: () => void
}) {
  const [hovered, setHovered] = useState<string | null>(null)
  const [drillLane, setDrillLane] = useState<string | null>(null)

  if (drillLane) {
    return <LaneDetailView laneId={drillLane} papers={papers} lanes={lanes} onBack={() => setDrillLane(null)} />
  }

  const W = 1200
  const H = 580
  const LM = 90
  const RM = 30
  const YEAR_MIN = 2019
  const YEAR_MAX = 2026.5
  const LANE_Y: Record<string, number> = { video_gen: 90, rl_based: 230, latent_space: 370, vla: 500 }

  function yearToX(year: number) { return LM + (year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN) * (W - LM - RM) }
  function nodeR(impact: number) { return impact >= 80 ? 7 : impact >= 60 ? 5 : 4 }

  type TrunkDef = { lane: string; yOff: number; width: number; opacity: number; nodes: { id: string; title: string; year: number; impact: number }[] }
  const TRUNKS: Record<string, TrunkDef> = {
    vg_diffusion: { lane: 'video_gen', yOff: 0, width: 3, opacity: 1, nodes: [
      { id: 'sora', title: 'Sora', year: 2024.0, impact: 78 },
      { id: 'drive_wm', title: 'Drive-WM', year: 2024.2, impact: 72 },
      { id: 'wan', title: 'Wan', year: 2025.2, impact: 45 },
      { id: 'cosmos', title: 'Cosmos', year: 2025.0, impact: 56 },
    ]},
    vg_interactive: { lane: 'video_gen', yOff: 30, width: 2, opacity: 0.5, nodes: [
      { id: 'gamenngen', title: 'GameNGen', year: 2024.5, impact: 57 },
      { id: 'genie2', title: 'Genie 2', year: 2024.8, impact: 55 },
    ]},
    vg_ar: { lane: 'video_gen', yOff: -25, width: 1.5, opacity: 0.4, nodes: [
      { id: 'emu3', title: 'Emu3', year: 2024.7, impact: 45 },
      { id: 'lwm', title: 'LWM', year: 2024.5, impact: 67 },
    ]},
    rl_rssm: { lane: 'rl_based', yOff: 0, width: 3, opacity: 1, nodes: [
      { id: 'planet', title: 'PlaNet', year: 2019.5, impact: 91 },
      { id: 'dreamer_v1', title: 'Dreamer V1', year: 2020.0, impact: 89 },
      { id: 'dreamer_v2', title: 'Dreamer V2', year: 2021.0, impact: 88 },
      { id: 'dreamer_v3', title: 'Dreamer V3', year: 2025.0, impact: 84 },
    ]},
    rl_mpc: { lane: 'rl_based', yOff: -28, width: 2, opacity: 0.5, nodes: [
      { id: 'tdmpc', title: 'TD-MPC', year: 2022.5, impact: 74 },
      { id: 'tdmpc2', title: 'TD-MPC2', year: 2024.5, impact: 71 },
    ]},
    rl_diffusion: { lane: 'rl_based', yOff: 28, width: 2, opacity: 0.5, nodes: [
      { id: 'diffuser', title: 'Diffuser', year: 2022.5, impact: 80 },
      { id: 'decision_diffuser', title: 'DecisionDiff', year: 2023.5, impact: 67 },
    ]},
    ls_jepa: { lane: 'latent_space', yOff: 0, width: 3, opacity: 1, nodes: [
      { id: 'i_jepa', title: 'I-JEPA', year: 2023.0, impact: 85 },
      { id: 'v_jepa', title: 'V-JEPA', year: 2024.0, impact: 80 },
      { id: 'v_jepa2', title: 'V-JEPA 2', year: 2025.0, impact: 51 },
    ]},
    ls_slot: { lane: 'latent_space', yOff: -28, width: 2, opacity: 0.5, nodes: [
      { id: 'slotattention', title: 'SlotAttn', year: 2020.5, impact: 92 },
      { id: 'slotformer', title: 'SlotFormer', year: 2023.5, impact: 74 },
    ]},
    vla_main: { lane: 'vla', yOff: 0, width: 3, opacity: 1, nodes: [
      { id: 'diffusion_policy', title: 'Diff Policy', year: 2023.0, impact: 88 },
      { id: 'pi0', title: 'π0', year: 2024.5, impact: 70 },
      { id: 'pi0_5', title: 'π0.5', year: 2025.0, impact: 55 },
    ]},
    vla_llm: { lane: 'vla', yOff: -25, width: 2, opacity: 0.5, nodes: [
      { id: 'rt2', title: 'RT-2', year: 2023.5, impact: 73 },
      { id: 'octo', title: 'Octo', year: 2024.0, impact: 72 },
    ]},
  }

  const FORKS: [string, string, number][] = [
    ['rl_mpc', 'rl_rssm', 2021.0],
    ['rl_diffusion', 'rl_rssm', 2021.0],
  ]

  type ConfDef = { id: string; title: string; year: number; lane: string; yOff: number; fromNodes: string[]; subtitle: string }
  const CONFLUENCES: ConfDef[] = [
    { id: 'unisim', title: 'UniSim', year: 2024.2, lane: 'rl_based', yOff: 35, fromNodes: ['dreamer_v3', 'sora'], subtitle: 'RL inside video WM' },
    { id: 'ar_dit', title: 'AR-DiT', year: 2025.2, lane: 'video_gen', yOff: 35, fromNodes: ['dreamer_v3', 'sora'], subtitle: 'diffusion goes causal' },
    { id: 'dreamgen', title: 'DreamGen', year: 2025.3, lane: 'rl_based', yOff: 35, fromNodes: ['dreamer_v3', 'cosmos'], subtitle: '22 behaviors / 1 demo' },
    { id: 'dreamzero', title: 'DreamDojo/Zero', year: 2025.8, lane: 'vla', yOff: 20, fromNodes: ['dreamer_v3', 'cosmos'], subtitle: '44K hrs + actions' },
  ]

  const nodePos: Record<string, { x: number; y: number }> = {}
  for (const [, trunk] of Object.entries(TRUNKS)) {
    const laneY = LANE_Y[trunk.lane] ?? 300
    for (const n of trunk.nodes) {
      nodePos[n.id] = { x: yearToX(n.year), y: laneY + trunk.yOff }
    }
  }
  for (const conf of CONFLUENCES) {
    nodePos[conf.id] = { x: yearToX(conf.year), y: (LANE_Y[conf.lane] ?? 300) + conf.yOff }
  }

  const laneList = [
    { id: 'video_gen', title: 'Video-Generative', color: '#2563EB' },
    { id: 'rl_based', title: 'RL-Based', color: '#059669' },
    { id: 'latent_space', title: 'Latent-Space', color: '#7C3AED' },
    { id: 'vla', title: 'Policy/VLA', color: '#EA580C' },
  ]

  return (
    <div style={{ fontFamily: "'IBM Plex Sans', sans-serif", background: '#FFFFFF', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '12px 32px', display: 'flex', alignItems: 'center', gap: 12, borderBottom: '1px solid #E4E4E7', background: '#FFF', flexShrink: 0 }}>
        <button type="button" onMouseDown={(e) => { e.preventDefault(); onBack() }} style={{ padding: '4px 12px', fontSize: 11, border: '1px solid #E4E4E7', cursor: 'pointer', background: '#FFF', color: '#3F3F46' }}>← Back</button>
        <span style={{ fontSize: 14, fontWeight: 600 }}>Trunks — Fork & Confluence</span>
        <span style={{ fontSize: 12, color: '#71717A' }}>主干=实线 · 分叉=贝塞尔弧 · 合流=菱形</span>
        <span style={{ marginLeft: 'auto', display: 'flex', gap: 14, fontSize: 11 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 14, height: 2, background: '#475569' }} />主干</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 14, height: 2, background: '#475569', borderTop: '1px dashed #475569' }} />分叉</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 14, height: 2, background: '#71717a', opacity: 0.5 }} />跨lane弧</span>
          <span style={{ color: '#EA580C', fontWeight: 600 }}>◇ 合流</span>
        </span>
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <svg viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', width: '100%', minWidth: 900, height: 'auto' }}>
          {/* Lane backgrounds (clickable) */}
          {laneList.map(lane => {
            const y = LANE_Y[lane.id] - 45
            return <g key={lane.id} style={{ cursor: 'pointer' }} onClick={() => setDrillLane(lane.id)}>
              <rect x={0} y={y} width={W} height={90} fill={lane.color} opacity={0.02} />
              <text x={10} y={LANE_Y[lane.id] - 32} fontSize={9} fill={lane.color} fontWeight={700} textDecoration="underline">{lane.title} →</text>
            </g>
          })}
          {/* Year grid */}
          {[2019,2020,2021,2022,2023,2024,2025,2026].map(yr => {
            const x = yearToX(yr)
            return <g key={yr}>
              <line x1={x} y1={15} x2={x} y2={H - 15} stroke="#e4e4e7" strokeWidth={0.5} />
              <text x={x} y={H - 4} textAnchor="middle" fontSize={8} fill="#a1a1aa">{yr}</text>
            </g>
          })}
          {/* Trunk lines */}
          {Object.entries(TRUNKS).map(([tid, trunk]) => {
            const laneY = LANE_Y[trunk.lane] ?? 300
            const ty = laneY + trunk.yOff
            const sorted = [...trunk.nodes].sort((a, b) => a.year - b.year)
            if (sorted.length < 1) return null
            const x1 = yearToX(sorted[0].year)
            const x2 = yearToX(sorted[sorted.length - 1].year)
            const color = laneList.find(l => l.id === trunk.lane)?.color || '#475569'
            return <path key={tid} d={`M${x1},${ty} L${x2},${ty}`} stroke={color} strokeWidth={trunk.width} fill="none" strokeLinecap="round" opacity={trunk.opacity} />
          })}
          {/* Fork arcs */}
          {FORKS.map(([forkTid, parentTid, forkYear], i) => {
            const forkTrunk = TRUNKS[forkTid]
            const parentTrunk = TRUNKS[parentTid]
            if (!forkTrunk || !parentTrunk) return null
            const parentY = (LANE_Y[parentTrunk.lane] ?? 300) + parentTrunk.yOff
            const forkY = (LANE_Y[forkTrunk.lane] ?? 300) + forkTrunk.yOff
            const forkX = yearToX(forkYear)
            const firstNode = [...forkTrunk.nodes].sort((a, b) => a.year - b.year)[0]
            const firstX = yearToX(firstNode.year)
            const color = laneList.find(l => l.id === forkTrunk.lane)?.color || '#475569'
            const midX = forkX + (firstX - forkX) * 0.4
            return <path key={`fork-${i}`} d={`M${forkX},${parentY} C${midX},${parentY} ${midX},${forkY} ${firstX},${forkY}`} stroke={color} strokeWidth={forkTrunk.width} fill="none" strokeLinecap="round" opacity={forkTrunk.opacity} />
          })}
          {/* Confluence arcs + diamonds */}
          {CONFLUENCES.map(conf => {
            const cx = nodePos[conf.id]?.x ?? 0
            const cy = nodePos[conf.id]?.y ?? 0
            const color = laneList.find(l => l.id === conf.lane)?.color || '#EA580C'
            return <g key={conf.id}>
              {conf.fromNodes.map(srcId => {
                const sp = nodePos[srcId]
                if (!sp) return null
                const mx = (sp.x + cx) / 2
                const srcColor = (() => { for (const [, t] of Object.entries(TRUNKS)) { if (t.nodes.some(n => n.id === srcId)) return laneList.find(l => l.id === t.lane)?.color } return '#71717a' })()
                return <path key={`conf-${conf.id}-${srcId}`} d={`M${sp.x},${sp.y} C${mx},${sp.y} ${mx},${cy} ${cx},${cy}`} stroke={srcColor} strokeWidth={1.5} fill="none" strokeLinecap="round" opacity={0.4} strokeDasharray="6 3" />
              })}
              <rect x={cx - 8} y={cy - 8} width={16} height={16} rx={2} fill="#fff" stroke={color} strokeWidth={2} transform={`rotate(45,${cx},${cy})`} />
              <text x={cx} y={cy + 20} textAnchor="middle" fontSize={7} fill={color} fontWeight={600}>{conf.title}</text>
              <text x={cx} y={cy + 29} textAnchor="middle" fontSize={6} fill="#71717a">{conf.subtitle}</text>
            </g>
          })}
          {/* Trunk nodes */}
          {Object.entries(TRUNKS).map(([tid, trunk]) => {
            const color = laneList.find(l => l.id === trunk.lane)?.color || '#475569'
            return trunk.nodes.map(n => {
              const p = nodePos[n.id]
              if (!p) return null
              const r = nodeR(n.impact)
              const isActive = hovered === n.id
              const op = n.impact >= 70 ? 0.8 : 0.5
              return <g key={n.id} style={{ cursor: 'pointer' }} onMouseEnter={() => setHovered(n.id)} onMouseLeave={() => setHovered(null)}>
                <circle cx={p.x} cy={p.y} r={isActive ? r + 2 : r} fill={color} opacity={op} stroke="#fff" strokeWidth={1.5} />
                <text x={p.x} y={p.y + r + 11} textAnchor="middle" fontSize={7} fill={color}>{n.title}</text>
              </g>
            })
          })}
        </svg>
      </div>
    </div>
  )
}

function LaneDetailView({ laneId, papers, lanes, onBack }: {
  laneId: string; papers: Paper[]; lanes: Lane[]; onBack: () => void
}) {
  const [hovered, setHovered] = useState<string | null>(null)
  const lane = lanes.find(l => l.id === laneId)
  const color = lane ? LANE_COLORS[lane.id] || '#475569' : '#475569'

  const lanePapers = papers.filter(p => p.lane === laneId)
  const YEAR_MIN = 2019
  const YEAR_MAX = 2026.5
  const W = 1200
  const ROW_H = 50
  const LM = 100
  const RM = 40
  const TM = 50

  const rows = [...new Set(lanePapers.map(p => p.row))]
  const H = TM + rows.length * ROW_H + 40

  function yearToX(year: number) { return LM + (year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN) * (W - LM - RM) }

  const nodePos: Record<string, { x: number; y: number }> = {}
  for (const p of lanePapers) {
    const rowIdx = rows.indexOf(p.row)
    const t = p.year + (p.quarter - 1) * 0.25
    nodePos[p.id] = { x: yearToX(t), y: TM + rowIdx * ROW_H + ROW_H / 2 }
  }

  type Edge = { from: string; to: string; type: 'inherits' | 'competes' | 'borrows' }
  const edges: Edge[] = []
  const visibleIds = new Set(lanePapers.map(p => p.id))
  for (const p of lanePapers) {
    if (p.connections) {
      for (const c of p.connections) {
        if (visibleIds.has(c.target)) edges.push({ from: c.target, to: p.id, type: c.type })
      }
    } else if (p.builds_on) {
      for (const srcId of p.builds_on) {
        if (visibleIds.has(srcId)) edges.push({ from: srcId, to: p.id, type: 'inherits' })
      }
    }
  }

  const edgeColor: Record<string, string> = { inherits: '#059669', competes: '#DC2626', borrows: '#7C3AED' }
  const edgeDash: Record<string, string | undefined> = { inherits: undefined, competes: '4 3', borrows: '2 3' }

  return (
    <div style={{ fontFamily: "'IBM Plex Sans', sans-serif", background: '#FFFFFF', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '12px 32px', display: 'flex', alignItems: 'center', gap: 12, borderBottom: '1px solid #E4E4E7', background: '#FFF', flexShrink: 0 }}>
        <button type="button" onMouseDown={(e) => { e.preventDefault(); onBack() }} style={{ padding: '4px 12px', fontSize: 11, border: '1px solid #E4E4E7', cursor: 'pointer', background: '#FFF', color: '#3F3F46' }}>← Back to Trunks</button>
        <span style={{ fontSize: 14, fontWeight: 600, color }}>{lane?.title}</span>
        <span style={{ fontSize: 12, color: '#71717A' }}>{lanePapers.length} papers · all connections</span>
        <span style={{ marginLeft: 'auto', display: 'flex', gap: 14, fontSize: 11 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 14, height: 2, background: '#059669' }} />inherits</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 14, height: 2, background: '#DC2626', borderTop: '1px dashed #DC2626' }} />competes</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 14, height: 2, background: '#7C3AED', borderTop: '1px dotted #7C3AED' }} />borrows</span>
        </span>
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <svg viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', width: '100%', minWidth: 900, height: 'auto' }}>
          {/* Year grid */}
          {[2019,2020,2021,2022,2023,2024,2025,2026].map(yr => {
            const x = yearToX(yr)
            return <g key={yr}>
              <line x1={x} y1={TM - 10} x2={x} y2={H} stroke="#F4F4F5" strokeWidth={1} />
              <text x={x} y={TM - 16} textAnchor="middle" fontSize={10} fontWeight={600} fill="#3F3F46">{yr}</text>
            </g>
          })}
          {/* Row labels */}
          {rows.map((rowId, idx) => {
            const y = TM + idx * ROW_H + ROW_H / 2
            return <g key={rowId}>
              <line x1={LM} y1={y} x2={W - RM} y2={y} stroke="#F4F4F5" strokeWidth={1} />
              <text x={LM - 8} y={y + 3} textAnchor="end" fontSize={8} fill="#71717A">{rowId.replace(/_/g, ' ')}</text>
            </g>
          })}
          {/* Edges */}
          {edges.map(({ from, to, type }, i) => {
            const p1 = nodePos[from], p2 = nodePos[to]
            if (!p1 || !p2) return null
            const isActive = hovered === from || hovered === to
            const sameRow = lanePapers.find(p => p.id === from)?.row === lanePapers.find(p => p.id === to)?.row
            if (sameRow) {
              return <line key={`e-${i}`} x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke={edgeColor[type]} strokeWidth={isActive ? 2 : 1.2} strokeOpacity={isActive ? 0.9 : 0.4} strokeDasharray={edgeDash[type]} />
            }
            const mx = (p1.x + p2.x) / 2
            return <path key={`e-${i}`} d={`M${p1.x},${p1.y} C${mx},${p1.y} ${mx},${p2.y} ${p2.x},${p2.y}`} fill="none" stroke={edgeColor[type]} strokeWidth={isActive ? 2 : 1.2} strokeOpacity={isActive ? 0.8 : 0.35} strokeDasharray={edgeDash[type] || '6 3'} />
          })}
          {/* Nodes */}
          {lanePapers.map(paper => {
            const p = nodePos[paper.id]
            if (!p) return null
            const impact = paper.impact_score ?? 0
            const r = impact >= 70 ? 6 : impact >= 50 ? 4.5 : 3
            const isActive = hovered === paper.id
            return <g key={paper.id} style={{ cursor: 'pointer' }} onMouseEnter={() => setHovered(paper.id)} onMouseLeave={() => setHovered(null)}>
              <circle cx={p.x} cy={p.y} r={isActive ? r + 1.5 : r} fill={color} opacity={impact >= 50 ? 0.8 : 0.35} stroke={isActive ? '#18181B' : '#fff'} strokeWidth={1.5} />
              {(isActive || impact >= 60) && <text x={p.x} y={p.y + r + 10} textAnchor="middle" fontSize={7} fill="#3F3F46">{paper.title}</text>}
            </g>
          })}
        </svg>
      </div>
    </div>
  )
}
