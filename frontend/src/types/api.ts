/**
 * TypeScript types for API communication
 */

export interface Node {
  id: string
  title: string
  cited_by_count: number
  publication_year: number
  community?: number
}

export interface Link {
  source: string
  target: string
}

export interface GraphMetadata {
  total_nodes: number
  total_links: number
  communities: number
  community_names: Record<string, string>
  avg_clustering?: number
}

export interface GraphResponse {
  nodes: Node[]
  links: Link[]
  metadata: GraphMetadata
}

export interface HealthResponse {
  status: string
  version: string
}

// ── Insight Report types ──────────────────────────────────────────

export interface Milestone {
  year: number
  paper_title: string
  contribution: string
}

export interface TemporalReport {
  stage: string
  timeline_desc: string
  key_milestones: Milestone[]
  year_range: string
}

export interface AuthorInfo {
  name: string
  paper_count: number
  total_citations: number
}

export interface InstitutionInfo {
  name: string
  paper_count: number
  category: string
}

export interface TalentReport {
  top_authors: AuthorInfo[]
  institutions: InstitutionInfo[]
  summary: string
}

export interface BottleneckReport {
  current_bottleneck: string
  existing_solutions: string[]
  next_directions: string[]
  summary: string
}

export interface InsightReport {
  path: string
  path_name: string
  temporal: TemporalReport
  talent: TalentReport
  bottleneck: BottleneckReport
  generated_at: string
  paper_count: number
}
