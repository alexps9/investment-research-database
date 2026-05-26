'use client'

import { useMemo, useState } from 'react'
import worldModelData from '@/data/world-model-data.json'

interface Connection { target: string; type: 'inherits' | 'competes' | 'borrows' }
interface Paper {
  id: string; title: string; year: number; quarter: number
  lane: string; row: string; path: string
  impact_score?: number | null
  shape?: 'circle' | 'square'
  builds_on: string[]
  connections?: Connection[]
  org?: string
  cited_by_count?: number
}
interface Lane { id: string; title: string; subtitle: string; color: string }
interface MapData { lanes: Lane[]; papers: Paper[] }

const data = worldModelData as unknown as MapData

const W = 1500
const H = 820
const X0 = 240
const X1 = W - 60
const Y_TOP = 150
const ROW_H = 160
const YEAR_START = 2019
const YEAR_END = 2027

function tx(year: number, q: number) {
  const t = year + (q - 1) * 0.25
  return X0 + (t - YEAR_START) / (YEAR_END - YEAR_START) * (X1 - X0)
}

const TRUNKS = [
  { id: 'rl_based',     title: 'RL / Imagination', sub: 'model-based, learn-by-dreaming', color: '#059669' },
  { id: 'video_gen',    title: 'Diffusion Video',  sub: 'pixel-level world generation',   color: '#2563EB' },
  { id: 'latent_space', title: 'JEPA / Latent',    sub: 'predict abstract representations', color: '#7C3AED' },
  { id: 'vla',          title: 'Policy / VLA',     sub: 'understanding to action',         color: '#EA580C' },
]

const REL_COLOR: Record<Connection['type'], string> = {
  inherits: '#059669',
  competes: '#DC2626',
  borrows:  '#7C3AED',
}
const REL_DASH: Record<Connection['type'], string | undefined> = {
  inherits: undefined,
  competes: '5 3',
  borrows:  '1 4',
}
const REL_LABEL: Record<Connection['type'], string> = {
  inherits: '继承',
  competes: '竞争',
  borrows:  '借鉴',
}

export default function WorldModelTrunks() {
  const [hovered, setHovered] = useState<string | null>(null)

  const milestonesPerLane = useMemo(() => {
    const map: Record<string, Paper[]> = {}
    for (const t of TRUNKS) {
      const inLane = data.papers.filter(p => p.lane === t.id && (p.impact_score ?? 0) >= 50)
      inLane.sort((a, b) => (b.impact_score ?? 0) - (a.impact_score ?? 0))
      map[t.id] = inLane.slice(0, 6)
    }
    return map
  }, [])

  const convergencePapers = useMemo(() => {
    const laneById = new Map(data.papers.map(p => [p.id, p.lane]))
    const result: Paper[] = []
    for (const p of data.papers) {
      const cn = p.connections || []
      if (cn.length < 2) continue
      const targetLanes = new Set<string>()
      for (const c of cn) {
        const tl = laneById.get(c.target)
        if (tl) targetLanes.add(tl)
      }
      if (targetLanes.size >= 2) result.push(p)
    }
    return result
  }, [])

  const trunkY = (laneId: string) => {
    const idx = TRUNKS.findIndex(t => t.id === laneId)
    return Y_TOP + idx * ROW_H
  }
  const trunkColor = (laneId: string) => TRUNKS.find(t => t.id === laneId)?.color ?? '#71717A'

  // Cross-lane edges (only ones to render)
  const crossEdges = useMemo(() => {
    const edges: { src: Paper; tgt: Paper; type: Connection['type'] }[] = []
    for (const p of data.papers) {
      for (const c of p.connections || []) {
        const tgt = data.papers.find(pp => pp.id === c.target)
        if (!tgt) continue
        if (tgt.lane === p.lane) continue
        edges.push({ src: tgt, tgt: p, type: c.type })
      }
    }
    return edges
  }, [])

  return (
    <div style={{ fontFamily: "'IBM Plex Sans', -apple-system, sans-serif", background: '#FFFFFF', minHeight: '100vh', padding: '32px 48px', overflowX: 'auto' }}>
      <div style={{ marginBottom: 12 }}>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: '#18181B' }}>World Model — 主干 × 汇流</h1>
        <p style={{ margin: '4px 0 0', fontSize: 12, color: '#71717A' }}>四条主干技术路径在哪里相遇。汇流点 = 同时引用 ≥ 2 条主干的论文。</p>
      </div>

      <div style={{ display: 'flex', gap: 28, fontSize: 11, color: '#3F3F46', margin: '20px 0 16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ width: 26, height: 6, background: '#3F3F46', borderRadius: 3 }} />主干</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ width: 12, height: 12, borderRadius: '50%', background: '#FFFFFF', border: '2.5px solid #18181B' }} />里程碑</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ color: '#EA580C', fontSize: 18, fontWeight: 700 }}>★</span><span>汇流点</span></span>
        <span style={{ width: 1, height: 14, background: '#E4E4E7' }} />
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><svg width="22" height="6"><line x1="0" y1="3" x2="22" y2="3" stroke="#059669" strokeWidth="2" /></svg>继承</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><svg width="22" height="6"><line x1="0" y1="3" x2="22" y2="3" stroke="#DC2626" strokeWidth="2" strokeDasharray="5 3" /></svg>竞争</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><svg width="22" height="6"><line x1="0" y1="3" x2="22" y2="3" stroke="#7C3AED" strokeWidth="2" strokeDasharray="1 4" /></svg>借鉴</span>
      </div>

      <div style={{ overflowX: 'auto', overflowY: 'hidden', maxWidth: '100%', WebkitOverflowScrolling: 'touch' }}>
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', background: '#FFFFFF', border: '1px solid #E4E4E7' }}>
        {/* Year vertical grid lines */}
        {Array.from({ length: YEAR_END - YEAR_START + 1 }, (_, i) => YEAR_START + i).map(y => {
          const x = tx(y, 1)
          return <g key={`grid-${y}`}>
            <line x1={x} y1={70} x2={x} y2={H - 36} stroke="#F4F4F5" strokeWidth={0.5} />
            <text x={x} y={H - 18} textAnchor="middle" fontSize={12} fontWeight={500} fill="#71717A">{y}</text>
          </g>
        })}

        {/* NOW marker */}
        <line x1={tx(2026, 2)} y1={70} x2={tx(2026, 2)} y2={H - 36} stroke="#FF4400" strokeWidth={1} strokeDasharray="4 3" />
        <text x={tx(2026, 2)} y={62} textAnchor="middle" fontSize={10} fontWeight={700} fill="#FF4400">NOW</text>

        {/* Trunks (thick lines, station-style) */}
        {TRUNKS.map(t => {
          const y = trunkY(t.id)
          const ms = milestonesPerLane[t.id] || []
          // Active range = first to last milestone, padded
          let activeX1 = X0, activeX2 = X1
          if (ms.length > 0) {
            const xs = ms.map(p => tx(p.year, p.quarter))
            activeX1 = Math.min(...xs) - 24
            activeX2 = Math.max(...xs) + 24
          }
          return <g key={`trunk-${t.id}`}>
            {/* Faint full line */}
            <line x1={X0} y1={y} x2={X1} y2={y} stroke="#E4E4E7" strokeWidth={1} />
            {/* Active thick segment */}
            <line x1={activeX1} y1={y} x2={activeX2} y2={y} stroke={t.color} strokeWidth={6} strokeLinecap="round" opacity={0.85} />
            {/* Lane label box */}
            <rect x={20} y={y - 26} width={200} height={52} rx={4} fill="#FFFFFF" stroke={t.color} strokeWidth={1.5} />
            <text x={30} y={y - 8} fontSize={14} fontWeight={700} fill={t.color}>{t.title}</text>
            <text x={30} y={y + 8} fontSize={9} fill="#71717A">{t.sub}</text>
            <text x={30} y={y + 20} fontSize={8} fill="#A1A1AA">{ms.length} milestones</text>
          </g>
        })}

        {/* Cross-lane edges (drawn before nodes so nodes sit on top) */}
        {crossEdges.map(({ src, tgt, type }, i) => {
          const x1 = tx(src.year, src.quarter), y1 = trunkY(src.lane)
          const x2 = tx(tgt.year, tgt.quarter), y2 = trunkY(tgt.lane)
          const isActive = hovered === src.id || hovered === tgt.id
          const color = REL_COLOR[type]
          const dash = REL_DASH[type]
          const midX = (x1 + x2) / 2
          // Smooth S-curve from src up/down to tgt
          return <path key={`xedge-${i}`}
            d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
            fill="none" stroke={color}
            strokeWidth={isActive ? 3 : 2}
            strokeDasharray={dash}
            opacity={isActive ? 0.95 : 0.6} />
        })}

        {/* Same-trunk inherits edges (between consecutive milestones) */}
        {TRUNKS.flatMap(t => {
          const ms = milestonesPerLane[t.id] || []
          const idsInLane = new Set(ms.map(p => p.id))
          const y = trunkY(t.id)
          const lines: React.ReactNode[] = []
          for (const p of ms) {
            for (const c of p.connections || []) {
              if (c.type !== 'inherits') continue
              if (!idsInLane.has(c.target)) continue
              const src = ms.find(x => x.id === c.target)
              if (!src) continue
              const x1 = tx(src.year, src.quarter)
              const x2 = tx(p.year, p.quarter)
              const isActive = hovered === src.id || hovered === p.id
              lines.push(
                <line key={`tr-${src.id}-${p.id}`} x1={x1} y1={y} x2={x2} y2={y}
                      stroke={t.color} strokeWidth={isActive ? 3 : 2.5} opacity={isActive ? 1 : 0.55} />
              )
            }
          }
          return lines
        })}

        {/* Milestone stations */}
        {TRUNKS.flatMap(t => {
          const ms = milestonesPerLane[t.id] || []
          const y = trunkY(t.id)
          return ms.map(p => {
            const x = tx(p.year, p.quarter)
            const isConv = convergencePapers.some(c => c.id === p.id)
            const isActive = hovered === p.id
            const r = isActive ? 9 : 8
            // Stagger label above/below to reduce overlap
            const idx = ms.indexOf(p)
            const labelAbove = idx % 2 === 0
            return <g key={`m-${p.id}`}
                onMouseEnter={() => setHovered(p.id)}
                onMouseLeave={() => setHovered(null)}
                style={{ cursor: 'pointer' }}>
              <circle cx={x} cy={y} r={r}
                      fill="#FFFFFF"
                      stroke={isConv ? '#EA580C' : t.color}
                      strokeWidth={isConv ? 3 : 2.5} />
              {isConv && <text x={x} y={y + 4} textAnchor="middle" fontSize={12} fill="#EA580C" fontWeight={700}>★</text>}
              <text x={x} y={labelAbove ? y - r - 6 : y + r + 14}
                    textAnchor="middle" fontSize={11}
                    fontWeight={isConv ? 700 : 600}
                    fill={isConv ? '#B45309' : '#18181B'}>{p.title}</text>
              {p.org && <text x={x} y={labelAbove ? y - r - 18 : y + r + 26}
                              textAnchor="middle" fontSize={9} fill="#A1A1AA">{p.org}</text>}
            </g>
          })
        })}

        {/* Extra convergence stars (papers that are convergence but NOT in lane top-6) */}
        {convergencePapers.filter(p =>
          !(milestonesPerLane[p.lane] || []).some(m => m.id === p.id)
        ).map(p => {
          const x = tx(p.year, p.quarter)
          const y = trunkY(p.lane)
          const isActive = hovered === p.id
          const r = isActive ? 10 : 9
          return <g key={`xstar-${p.id}`}
              onMouseEnter={() => setHovered(p.id)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: 'pointer' }}>
            <circle cx={x} cy={y} r={r} fill="#FFFFFF" stroke="#EA580C" strokeWidth={3} />
            <text x={x} y={y + 4} textAnchor="middle" fontSize={13} fill="#EA580C" fontWeight={700}>★</text>
            <text x={x} y={y - r - 6} textAnchor="middle" fontSize={11} fontWeight={700} fill="#B45309">{p.title}</text>
            {p.org && <text x={x} y={y - r - 18} textAnchor="middle" fontSize={9} fill="#A1A1AA">{p.org}</text>}
          </g>
        })}
      </svg>
      </div>

      <div style={{ marginTop: 16, fontSize: 11, color: '#71717A', lineHeight: 1.6 }}>
        <div><b>筛选规则</b>：每条主干取 impact_score ≥ 50 的 top-6 作为 milestone 站点；汇流 ★ = connections 跨 ≥ 2 个 lane 的论文（自动检测，共 {convergencePapers.length} 个）。</div>
        <div><b>读图</b>：横线 = 主干（持续演化路径）；S 形跨线 = 跨 lane 引用（融合证据）；★ = 多主干汇流的论文，下次会议重点。</div>
      </div>
    </div>
  )
}
