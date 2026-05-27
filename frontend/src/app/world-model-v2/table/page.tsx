'use client'

import { useState, useEffect, useMemo } from 'react'
import { fetchWorldModel, updatePaper, deletePaper, Paper, Lane, Row, WorldModelData } from '@/lib/api'

type SortKey = 'title' | 'year' | 'lane' | 'row' | 'impact_score' | 'cited_by_count' | 'org'
type SortDir = 'asc' | 'desc'

export default function TablePage() {
  const [data, setData] = useState<WorldModelData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const [filterLane, setFilterLane] = useState<string>('')
  const [filterRow, setFilterRow] = useState<string>('')
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('impact_score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValues, setEditValues] = useState<Record<string, any>>({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchWorldModel()
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const laneMap = useMemo(() => {
    if (!data) return {} as Record<string, Lane>
    return Object.fromEntries(data.lanes.map(l => [l.id, l]))
  }, [data])

  const rowMap = useMemo(() => {
    if (!data) return {} as Record<string, Row>
    return Object.fromEntries(data.rows.map(r => [r.id, r]))
  }, [data])

  const filtered = useMemo(() => {
    if (!data) return []
    let papers = [...data.papers]
    if (filterLane) papers = papers.filter(p => p.lane === filterLane)
    if (filterRow) papers = papers.filter(p => p.row === filterRow)
    if (search) {
      const q = search.toLowerCase()
      papers = papers.filter(p =>
        p.title.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q) ||
        (p.org || '').toLowerCase().includes(q)
      )
    }
    papers.sort((a, b) => {
      const av = a[sortKey] ?? 0
      const bv = b[sortKey] ?? 0
      if (av < bv) return sortDir === 'asc' ? -1 : 1
      if (av > bv) return sortDir === 'asc' ? 1 : -1
      return 0
    })
    return papers
  }, [data, filterLane, filterRow, search, sortKey, sortDir])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const startEdit = (paper: Paper) => {
    setEditingId(paper.id)
    setEditValues({
      impact_score: paper.impact_score ?? '',
      impact_override: paper.impact_override ?? '',
      lane: paper.lane,
      row: paper.row,
      org: paper.org ?? '',
      year: paper.year,
      quarter: paper.quarter,
    })
  }

  const cancelEdit = () => { setEditingId(null); setEditValues({}) }

  const saveEdit = async () => {
    if (!editingId || !data) return
    setSaving(true)
    try {
      const updates: Record<string, any> = {}
      const orig = data.papers.find(p => p.id === editingId)!
      if (editValues.impact_override !== '' && editValues.impact_override !== orig.impact_override) {
        updates.impact_override = Number(editValues.impact_override)
      }
      if (editValues.lane !== orig.lane) updates.lane = editValues.lane
      if (editValues.row !== orig.row) updates.row = editValues.row
      if (editValues.org !== (orig.org ?? '')) updates.org = editValues.org || null
      if (Number(editValues.year) !== orig.year) updates.year = Number(editValues.year)
      if (Number(editValues.quarter) !== orig.quarter) updates.quarter = Number(editValues.quarter)

      if (Object.keys(updates).length > 0) {
        const updated = await updatePaper(editingId, updates)
        setData(prev => prev ? {
          ...prev,
          papers: prev.papers.map(p => p.id === editingId ? { ...p, ...updated } : p)
        } : prev)
      }
      setEditingId(null)
      setEditValues({})
    } catch (e: any) {
      alert(`Save failed: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(`Delete paper "${id}"?`)) return
    try {
      await deletePaper(id)
      setData(prev => prev ? { ...prev, papers: prev.papers.filter(p => p.id !== id) } : prev)
    } catch (e: any) {
      alert(`Delete failed: ${e.message}`)
    }
  }

  const availableRows = useMemo(() => {
    if (!data) return []
    if (!filterLane) return data.rows
    return data.rows.filter(r => r.lane === filterLane)
  }, [data, filterLane])

  if (loading) return <div style={{ padding: 40, fontFamily: 'IBM Plex Sans, sans-serif' }}>Loading...</div>
  if (error) return <div style={{ padding: 40, fontFamily: 'IBM Plex Sans, sans-serif', color: '#DC2626' }}>Error: {error}</div>
  if (!data) return null

  return (
    <div style={{ fontFamily: 'IBM Plex Sans, sans-serif', padding: '16px 24px', maxWidth: 1400, margin: '0 auto' }}>
      <Header count={filtered.length} total={data.papers.length} />
      <Filters
        lanes={data.lanes}
        rows={availableRows}
        filterLane={filterLane}
        filterRow={filterRow}
        search={search}
        onLaneChange={setFilterLane}
        onRowChange={setFilterRow}
        onSearchChange={setSearch}
      />
      <Table
        papers={filtered}
        laneMap={laneMap}
        rowMap={rowMap}
        sortKey={sortKey}
        sortDir={sortDir}
        onSort={handleSort}
        editingId={editingId}
        editValues={editValues}
        saving={saving}
        onStartEdit={startEdit}
        onCancelEdit={cancelEdit}
        onSaveEdit={saveEdit}
        onEditChange={(k, v) => setEditValues(prev => ({ ...prev, [k]: v }))}
        onDelete={handleDelete}
        lanes={data.lanes}
        rows={availableRows}
      />
    </div>
  )
}

// ─── Sub-components ──────────────────────────────────────────────

function Header({ count, total }: { count: number; total: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 12 }}>
      <h1 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>Papers</h1>
      <span style={{ fontSize: 12, color: '#71717A' }}>
        {count === total ? `${total} papers` : `${count} / ${total} papers`}
      </span>
      <a href="/world-model-v2" style={{ marginLeft: 'auto', fontSize: 12, color: '#2563EB', textDecoration: 'none' }}>
        ← Map View
      </a>
    </div>
  )
}

function Filters({ lanes, rows, filterLane, filterRow, search, onLaneChange, onRowChange, onSearchChange }: {
  lanes: Lane[]; rows: Row[]
  filterLane: string; filterRow: string; search: string
  onLaneChange: (v: string) => void; onRowChange: (v: string) => void; onSearchChange: (v: string) => void
}) {
  const inputStyle: React.CSSProperties = {
    fontSize: 12, padding: '4px 8px', border: '1px solid #E4E4E7',
    borderRadius: 4, outline: 'none', fontFamily: 'inherit',
  }
  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap', alignItems: 'center' }}>
      <select value={filterLane} onChange={e => { onLaneChange(e.target.value); onRowChange('') }} style={inputStyle}>
        <option value="">All Lanes</option>
        {lanes.map(l => <option key={l.id} value={l.id}>{l.title}</option>)}
      </select>
      <select value={filterRow} onChange={e => onRowChange(e.target.value)} style={inputStyle}>
        <option value="">All Rows</option>
        {rows.map(r => <option key={r.id} value={r.id}>{r.title}</option>)}
      </select>
      <input
        type="text" placeholder="Search title / id / org..."
        value={search} onChange={e => onSearchChange(e.target.value)}
        style={{ ...inputStyle, width: 200 }}
      />
    </div>
  )
}

function Table({ papers, laneMap, rowMap, sortKey, sortDir, onSort, editingId, editValues, saving,
  onStartEdit, onCancelEdit, onSaveEdit, onEditChange, onDelete, lanes, rows }: {
  papers: Paper[]; laneMap: Record<string, Lane>; rowMap: Record<string, Row>
  sortKey: SortKey; sortDir: SortDir; onSort: (k: SortKey) => void
  editingId: string | null; editValues: Record<string, any>; saving: boolean
  onStartEdit: (p: Paper) => void; onCancelEdit: () => void; onSaveEdit: () => void
  onEditChange: (k: string, v: any) => void; onDelete: (id: string) => void
  lanes: Lane[]; rows: Row[]
}) {
  const thStyle: React.CSSProperties = {
    padding: '6px 8px', fontSize: 11, fontWeight: 600, color: '#3F3F46',
    borderBottom: '1px solid #E4E4E7', textAlign: 'left', cursor: 'pointer',
    whiteSpace: 'nowrap', userSelect: 'none',
  }
  const tdStyle: React.CSSProperties = {
    padding: '5px 8px', fontSize: 12, borderBottom: '1px solid #F4F4F5',
    whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 200,
  }
  const arrow = (key: SortKey) => sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={thStyle} onClick={() => onSort('title')}>Title{arrow('title')}</th>
            <th style={thStyle} onClick={() => onSort('year')}>Year{arrow('year')}</th>
            <th style={thStyle} onClick={() => onSort('lane')}>Lane{arrow('lane')}</th>
            <th style={thStyle} onClick={() => onSort('row')}>Row{arrow('row')}</th>
            <th style={thStyle} onClick={() => onSort('impact_score')}>Impact{arrow('impact_score')}</th>
            <th style={thStyle} onClick={() => onSort('cited_by_count')}>Citations{arrow('cited_by_count')}</th>
            <th style={thStyle} onClick={() => onSort('org')}>Org{arrow('org')}</th>
            <th style={{ ...thStyle, cursor: 'default' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {papers.map(p => (
            <TableRow
              key={p.id} paper={p} laneMap={laneMap} rowMap={rowMap}
              isEditing={editingId === p.id} editValues={editValues} saving={saving}
              onStartEdit={() => onStartEdit(p)} onCancelEdit={onCancelEdit}
              onSaveEdit={onSaveEdit} onEditChange={onEditChange}
              onDelete={() => onDelete(p.id)} lanes={lanes} rows={rows}
              tdStyle={tdStyle}
            />
          ))}
        </tbody>
      </table>
      {papers.length === 0 && (
        <div style={{ padding: 24, textAlign: 'center', color: '#A1A1AA', fontSize: 13 }}>No papers found</div>
      )}
    </div>
  )
}

function TableRow({ paper, laneMap, rowMap, isEditing, editValues, saving,
  onStartEdit, onCancelEdit, onSaveEdit, onEditChange, onDelete, lanes, rows, tdStyle }: {
  paper: Paper; laneMap: Record<string, Lane>; rowMap: Record<string, Row>
  isEditing: boolean; editValues: Record<string, any>; saving: boolean
  onStartEdit: () => void; onCancelEdit: () => void; onSaveEdit: () => void
  onEditChange: (k: string, v: any) => void; onDelete: () => void
  lanes: Lane[]; rows: Row[]; tdStyle: React.CSSProperties
}) {
  const cellInput: React.CSSProperties = {
    fontSize: 11, padding: '2px 4px', border: '1px solid #E4E4E7', borderRadius: 3, width: 60,
  }
  const btnStyle: React.CSSProperties = {
    fontSize: 11, padding: '2px 6px', border: '1px solid #E4E4E7', borderRadius: 3,
    background: '#fff', cursor: 'pointer', fontFamily: 'inherit',
  }

  if (isEditing) {
    return (
      <tr style={{ background: '#FAFAFA' }}>
        <td style={tdStyle}>{paper.title}</td>
        <td style={tdStyle}>
          <input type="number" value={editValues.year} onChange={e => onEditChange('year', e.target.value)} style={{ ...cellInput, width: 50 }} />
          Q<input type="number" min={1} max={4} value={editValues.quarter} onChange={e => onEditChange('quarter', e.target.value)} style={{ ...cellInput, width: 30 }} />
        </td>
        <td style={tdStyle}>
          <select value={editValues.lane} onChange={e => onEditChange('lane', e.target.value)} style={{ ...cellInput, width: 90 }}>
            {lanes.map(l => <option key={l.id} value={l.id}>{l.title}</option>)}
          </select>
        </td>
        <td style={tdStyle}>
          <select value={editValues.row} onChange={e => onEditChange('row', e.target.value)} style={{ ...cellInput, width: 100 }}>
            {rows.map(r => <option key={r.id} value={r.id}>{r.title}</option>)}
          </select>
        </td>
        <td style={tdStyle}>
          <input type="number" value={editValues.impact_override} placeholder="override"
            onChange={e => onEditChange('impact_override', e.target.value)} style={{ ...cellInput, width: 50 }} />
          <span style={{ fontSize: 10, color: '#A1A1AA', marginLeft: 4 }}>({paper.impact_score?.toFixed(0) ?? '—'})</span>
        </td>
        <td style={tdStyle}>{paper.cited_by_count ?? '—'}</td>
        <td style={tdStyle}>
          <input value={editValues.org} onChange={e => onEditChange('org', e.target.value)} style={{ ...cellInput, width: 80 }} />
        </td>
        <td style={tdStyle}>
          <button onClick={onSaveEdit} disabled={saving} style={{ ...btnStyle, color: '#059669' }}>Save</button>
          <button onClick={onCancelEdit} style={{ ...btnStyle, marginLeft: 4 }}>Cancel</button>
        </td>
      </tr>
    )
  }

  const lane = laneMap[paper.lane]
  return (
    <tr>
      <td style={tdStyle} title={paper.id}>
        {paper.arxiv_id ? (
          <a href={`https://arxiv.org/abs/${paper.arxiv_id}`} target="_blank" rel="noopener noreferrer"
            style={{ color: '#18181B', textDecoration: 'none', borderBottom: '1px dashed #E4E4E7' }}>
            {paper.title}
          </a>
        ) : paper.title}
      </td>
      <td style={tdStyle}>{paper.year} Q{paper.quarter}</td>
      <td style={tdStyle}>
        <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: lane?.color || '#A1A1AA', marginRight: 4 }} />
        {lane?.title || paper.lane}
      </td>
      <td style={tdStyle}>{rowMap[paper.row]?.title || paper.row}</td>
      <td style={tdStyle}>
        <ImpactBar score={paper.impact_score} override={paper.impact_override} />
      </td>
      <td style={tdStyle}>{paper.cited_by_count ?? '—'}</td>
      <td style={tdStyle}>{paper.org || '—'}</td>
      <td style={tdStyle}>
        <button onClick={onStartEdit} style={btnStyle}>Edit</button>
        <button onClick={onDelete} style={{ ...btnStyle, marginLeft: 4, color: '#DC2626' }}>Del</button>
      </td>
    </tr>
  )
}

function ImpactBar({ score, override }: { score?: number | null; override?: number | null }) {
  const val = override ?? score ?? 0
  const color = val >= 70 ? '#059669' : val >= 50 ? '#2563EB' : '#A1A1AA'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      <div style={{ width: 40, height: 4, background: '#F4F4F5', borderRadius: 2 }}>
        <div style={{ width: `${val}%`, height: '100%', background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 11, color }}>{val.toFixed(0)}</span>
      {override != null && <span style={{ fontSize: 9, color: '#EA580C' }}>*</span>}
    </div>
  )
}
