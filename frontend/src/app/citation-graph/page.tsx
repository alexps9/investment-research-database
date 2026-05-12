'use client'

import { useMemo, useState } from 'react'
import CitationGraph from '@/components/CitationGraph/CitationGraph'
import SidePanel from '@/components/SidePanel/SidePanel'
import { LANE_IDS, LANES } from '@/lib/citation-graph/constants'
import { SEED_DATA } from '@/lib/citation-graph/seed-data'
import { MOCK_ASSESSMENTS } from '@/lib/citation-graph/mock-assessments'
import type { LaneId } from '@/types/citation-graph'
import styles from './page.module.css'

type LaneFilter = 'all' | LaneId

export default function CitationGraphPage() {
  const [filter, setFilter] = useState<LaneFilter>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const data = useMemo(() => {
    if (filter === 'all') return SEED_DATA
    const nodes = SEED_DATA.nodes.filter((n) => n.lane === filter)
    const ids = new Set(nodes.map((n) => n.id))
    const links = SEED_DATA.links.filter((l) => ids.has(l.source) && ids.has(l.target))
    return { nodes, links }
  }, [filter])

  const selectedNode = useMemo(
    () => (selectedId ? SEED_DATA.nodes.find((n) => n.id === selectedId) ?? null : null),
    [selectedId],
  )
  const assessment = useMemo(
    () => (selectedId ? MOCK_ASSESSMENTS[selectedId] ?? null : null),
    [selectedId],
  )

  const stats = useMemo(() => {
    return {
      nodes: data.nodes.length,
      links: data.links.length,
      tier1: data.nodes.filter((n) => n.tier === 1).length,
    }
  }, [data])

  return (
    <div className={styles.layout}>
      <main className={styles.main}>
        <TopBar filter={filter} onFilter={setFilter} />
        <div className={styles.graphHost}>
          <CitationGraph data={data} selectedId={selectedId} onSelect={setSelectedId} />
        </div>
        <StatusBar stats={stats} />
      </main>
      <SidePanel
        node={selectedNode}
        assessment={assessment}
        onClose={() => setSelectedId(null)}
      />
    </div>
  )
}

function TopBar({
  filter,
  onFilter,
}: {
  filter: LaneFilter
  onFilter: (f: LaneFilter) => void
}) {
  return (
    <div className={styles.topBar}>
      <div className={styles.brand}>
        <h1 className={styles.brandTitle}>
          LLM Arch <span className={styles.brandOrange}>/ Citation Graph</span>
        </h1>
        <span className={styles.brandSub}>Scheme B · 2023 Q1 → 2026 Q4</span>
      </div>
      <div className={styles.filters}>
        <button
          type="button"
          className={`${styles.filterBtn}${filter === 'all' ? ` ${styles.filterBtnActive}` : ''}`}
          onClick={() => onFilter('all')}
        >
          All
        </button>
        {LANE_IDS.map((id) => (
          <button
            key={id}
            type="button"
            className={`${styles.filterBtn}${filter === id ? ` ${styles.filterBtnActive}` : ''}`}
            onClick={() => onFilter(id)}
          >
            L{id} · {LANES[id].title.split(' ')[0]}
          </button>
        ))}
      </div>
    </div>
  )
}

function StatusBar({
  stats,
}: {
  stats: { nodes: number; links: number; tier1: number }
}) {
  return (
    <div className={styles.statusBar}>
      <span>
        <span className={styles.statusDot} /> live · mock data
      </span>
      <span className={styles.statusDivider}>|</span>
      <span>{stats.nodes} papers</span>
      <span className={styles.statusDivider}>|</span>
      <span>{stats.links} citations</span>
      <span className={styles.statusDivider}>|</span>
      <span>{stats.tier1} tier-1</span>
      <span className={styles.statusDivider}>|</span>
      <span>
        <span className={styles.legendBadge} style={{ color: '#ff4400' }}>
          ●
        </span>
        α-high = paradigm shift
      </span>
      <span className={styles.statusDivider}>|</span>
      <span>node area ∝ log(citations)</span>
    </div>
  )
}
