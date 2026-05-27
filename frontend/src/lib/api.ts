const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface Lane {
  id: string
  title: string
  subtitle: string
  color: string
}

export interface Row {
  id: string
  lane: string
  title: string
  subtitle: string
}

export interface Connection {
  target: string
  type: 'inherits' | 'competes' | 'borrows'
}

export interface Paper {
  id: string
  title: string
  full_title?: string | null
  year: number
  quarter: number
  lane: string
  row: string
  path: string
  paradigm?: string | null
  layer?: string | null
  shape?: 'circle' | 'square'
  org?: string | null
  authors?: string[]
  arxiv_id?: string | null
  doi?: string | null
  cited_by_count?: number | null
  venue_tier?: number | null
  institution_tier?: number | null
  impact_score?: number | null
  impact_override?: number | null
  connections?: Connection[]
  builds_on?: string[]
  is_rising?: boolean
  is_weak_signal?: boolean
}

export interface WorldModelData {
  lanes: Lane[]
  rows: Row[]
  papers: Paper[]
}

export async function fetchWorldModel(): Promise<WorldModelData> {
  const res = await fetch(`${API_BASE}/api/world-model`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function updatePaper(
  paperId: string,
  updates: Partial<Omit<Paper, 'id' | 'connections' | 'builds_on'>>
): Promise<Paper> {
  const res = await fetch(`${API_BASE}/api/world-model/papers/${paperId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  })
  if (!res.ok) throw new Error(`Update failed: ${res.status}`)
  return res.json()
}

export async function deletePaper(paperId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/world-model/papers/${paperId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`)
}

export async function createPaper(
  paper: Omit<Paper, 'connections' | 'builds_on' | 'is_rising' | 'is_weak_signal'>
): Promise<Paper> {
  const res = await fetch(`${API_BASE}/api/world-model/papers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(paper),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Create failed: ${res.status}`)
  }
  return res.json()
}
