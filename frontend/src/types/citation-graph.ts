// Types for the citation-graph visualization (Scheme B).
// See .claude/docs/specs/citation-graph-spec.md §6.

export type LaneId = 1 | 2 | 3
export type SubLane = 'A' | 'B' | 'C'
export type Tier = 1 | 2
export type Alpha = 'high' | 'mid' | 'low'
export type Quarter = 1 | 2 | 3 | 4

export interface GraphNode {
  id: string
  title: string
  authors: string[]
  year: number
  quarter: Quarter
  lane: LaneId
  sub_lane: SubLane
  tier: Tier
  cited_by_count: number
  arxiv_id?: string
  source_url?: string
  is_pre_2023: boolean
  alpha?: Alpha
  tags: string[]
  note?: string
}

export interface GraphLink {
  source: string
  target: string
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

export interface LaneDef {
  id: LaneId
  title: string
  question: string
  color: string
  fill: string
  subLanes: Record<SubLane, SubLaneDef>
}

export interface SubLaneDef {
  id: SubLane
  title: string
  question: string
}

// Tier-1 rich assessment data (optional; shown when clicking a tier-1 node).
// Matches demo-preview.html 7-module structure but in Rams skin.
export interface TechAssessment {
  positioning: {
    role: string
    benchmark: string
    coreDiff: string
    isParadigmShift?: boolean
  }
  evolution: {
    predecessors: string[]
    current: string
    successors: string[]
  }
  stageDetail: {
    phase: string
    period: string
    signals: string[]
  }
  growth?: string
  players: {
    coreResearchers: Array<{ name: string; affiliation: string }>
    activeTeams: string[]
  }
  bottlenecks: {
    current: string[]
    unsolved: string[]
  }
  conclusion: string
}
