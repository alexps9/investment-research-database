'use client'

import { useCallback, useMemo, useState, useRef, useEffect } from 'react'
import dynamic from 'next/dynamic'
import type { GraphResponse, Node as GraphNode } from '@/types/api'
import styles from './ForceGraph.module.css'

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false })

export interface ForceGraphProps {
  data: GraphResponse
  onNodeClick?: (node: GraphNode) => void
  width?: number
  height?: number
  topNodeIds?: Set<string>
  layoutMode?: 'timeline' | 'cluster'
}

// Brighter colors for dark background
const COMMUNITY_COLORS = [
  '#6CA4DC', // bright blue
  '#D4956A', // warm orange
  '#7FC47F', // green
  '#C49BDE', // lavender
  '#D4C36A', // gold
  '#6DC4C4', // cyan
  '#DE7E7E', // coral
  '#8CB8DE', // sky blue
]

const BG_COLOR = '#1A1A2E'

interface GraphNodeInternal {
  id: string
  title: string
  cited_by_count: number
  publication_year: number
  community: number
  x?: number
  y?: number
  vx?: number
  vy?: number
}

export default function ForceGraph({
  data,
  onNodeClick,
  width = 800,
  height = 600,
  topNodeIds,
  layoutMode = 'timeline',
}: ForceGraphProps) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const neighborMapRef = useRef<Map<string, Set<string>>>(new Map())
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null)

  const yearRange = useMemo(() => {
    const years = data.nodes.map(n => n.publication_year).filter(y => y > 1950)
    if (years.length === 0) return { min: 2015, max: 2026 }
    return { min: Math.min(...years), max: Math.max(...years) }
  }, [data])

  const communityNames = useMemo(() => data.metadata.community_names ?? {}, [data])

  const communityCount = useMemo(() => {
    if (!data.nodes.length) return 0
    return Math.max(...data.nodes.map(n => (n.community ?? 0))) + 1
  }, [data])

  // Pre-compute layout params: year→X, community→Y mapping
  const layoutParams = useMemo(() => {
    const padding = 80
    const usableWidth = width - padding * 2
    const usableHeight = height - padding * 2
    const yearSpan = Math.max(1, yearRange.max - yearRange.min)
    const halfW = width / 2
    const halfH = height / 2

    // Give each community a generous Y band (swim lane)
    const laneHeight = usableHeight / Math.max(communityCount, 1)
    const communityYPositions = new Map<number, number>()
    for (let i = 0; i < communityCount; i++) {
      // Center of each lane
      const y = padding + (i + 0.5) * laneHeight - halfH
      communityYPositions.set(i, y)
    }
    return { padding, usableWidth, usableHeight, yearSpan, halfW, halfH, laneHeight, communityYPositions }
  }, [width, height, yearRange, communityCount])

  const graphData = useMemo(() => {
    const neighbors = new Map<string, Set<string>>()
    data.nodes.forEach(n => neighbors.set(n.id, new Set()))
    data.links.forEach(link => {
      neighbors.get(link.source)?.add(link.target)
      neighbors.get(link.target)?.add(link.source)
    })
    neighborMapRef.current = neighbors

    const { padding, usableWidth, yearSpan, halfW, communityYPositions } = layoutParams

    // Count nodes per (community, year) bucket for vertical spreading
    const bucketCount = new Map<string, number>()
    const bucketIndex = new Map<string, number>()
    data.nodes.forEach(n => {
      const key = `${n.community ?? 0}_${n.publication_year}`
      bucketCount.set(key, (bucketCount.get(key) ?? 0) + 1)
    })

    const nodes = data.nodes.map(node => {
      const comm = node.community ?? 0
      const year = node.publication_year > 1950 ? node.publication_year : yearRange.min
      // X: fixed by year
      const fx = padding + ((year - yearRange.min) / yearSpan) * usableWidth - halfW

      // Y: community band + vertical spread within band
      const key = `${comm}_${node.publication_year}`
      const idx = bucketIndex.get(key) ?? 0
      bucketIndex.set(key, idx + 1)
      const total = bucketCount.get(key) ?? 1
      const baseY = communityYPositions.get(comm) ?? 0
      const spread = 28
      const fy = baseY + (idx - (total - 1) / 2) * spread

      if (layoutMode === 'cluster') {
        // In cluster mode: use computed positions as initial hints only, no fixed positions
        return {
          id: node.id,
          title: node.title,
          cited_by_count: node.cited_by_count,
          publication_year: node.publication_year,
          community: comm,
          x: fx, y: fy,
        }
      }

      return {
        id: node.id,
        title: node.title,
        cited_by_count: node.cited_by_count,
        publication_year: node.publication_year,
        community: comm,
        fx, fy,  // fixed positions — no simulation drift
        x: fx, y: fy,
      }
    })

    return {
      nodes,
      links: data.links.map(link => ({
        source: link.target,
        target: link.source,
      })),
    }
  }, [data, layoutParams, yearRange, layoutMode])

  // Configure forces based on layout mode
  useEffect(() => {
    const fg = fgRef.current
    if (!fg) return

    if (layoutMode === 'timeline') {
      // Timeline: disable all simulation forces — positions are fixed
      fg.d3Force('center', null)
      fg.d3Force('charge', null)
      fg.d3Force('link')?.strength(0)
      fg.d3Force('community', null)
    } else {
      // Cluster mode: enable physics simulation with community clustering
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const d3 = (window as any).d3
      if (d3) {
        fg.d3Force('center', d3.forceCenter())
      }
      fg.d3Force('charge')?.strength(-80)
      fg.d3Force('link')?.distance(40).strength(0.3)

      // Community clustering force: pull nodes toward community centroid (Y axis)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const communityForce = (alpha: number) => {
        const nodes = fg.graphData().nodes as GraphNodeInternal[]
        // Compute community Y centroids
        const centroidY = new Map<number, { sum: number; count: number }>()
        nodes.forEach(n => {
          if (n.y === undefined) return
          const entry = centroidY.get(n.community) ?? { sum: 0, count: 0 }
          entry.sum += n.y
          entry.count++
          centroidY.set(n.community, entry)
        })
        nodes.forEach(n => {
          if (n.vy === undefined) return
          const entry = centroidY.get(n.community)
          if (!entry || entry.count === 0) return
          const cy = entry.sum / entry.count
          n.vy! += (cy - (n.y ?? 0)) * alpha * 0.5
        })
      }
      fg.d3Force('community', communityForce)

      // Reheat the simulation
      fg.d3ReheatSimulation()
    }
  }, [graphData, layoutMode])

  const isTopNode = useCallback((id: string) => topNodeIds?.has(id) ?? false, [topNodeIds])

  const isHighlighted = useCallback((nodeId: string) => {
    if (!hoveredNode) return true
    if (nodeId === hoveredNode) return true
    return neighborMapRef.current.get(hoveredNode)?.has(nodeId) ?? false
  }, [hoveredNode])

  const nodeCanvasObject = useCallback((node: unknown, ctx: CanvasRenderingContext2D) => {
    const n = node as GraphNodeInternal
    if (n.x === undefined || n.y === undefined) return

    const citedBy = n.cited_by_count || 0
    const baseSize = Math.max(2, Math.min(8, Math.log(citedBy + 1) * 1.5))
    const isTop = isTopNode(n.id)
    const size = isTop ? baseSize * 1.3 : baseSize
    const highlighted = isHighlighted(n.id)
    const alpha = highlighted ? 1 : 0.12

    const color = COMMUNITY_COLORS[n.community % COMMUNITY_COLORS.length]

    ctx.globalAlpha = alpha
    ctx.beginPath()
    ctx.arc(n.x, n.y, size, 0, 2 * Math.PI)
    ctx.fillStyle = color
    ctx.fill()

    if (isTop) {
      ctx.strokeStyle = '#FF4400'
      ctx.lineWidth = 1.5
      ctx.stroke()
    }

    // Permanent label for top nodes; hover label for all nodes
    const showLabel = isTop || n.id === hoveredNode
    if (showLabel) {
      const maxChars = isTop ? 38 : 45
      const label = n.title.length > maxChars ? n.title.slice(0, maxChars - 3) + '...' : n.title
      const fontSize = isTop ? 9.5 : 10
      ctx.font = `${isTop ? '600 ' : ''}${fontSize}px -apple-system, Helvetica, Arial, sans-serif`
      const textWidth = ctx.measureText(label).width
      const pad = 3
      const lx = n.x - textWidth / 2
      const ly = n.y + size + 4

      // Background pill
      ctx.globalAlpha = isTop ? 0.82 : 0.9
      ctx.fillStyle = isTop ? '#1A1A2E' : '#000000'
      ctx.beginPath()
      ctx.roundRect(lx - pad, ly - pad, textWidth + pad * 2, fontSize + pad * 2, 2)
      ctx.fill()

      // Text
      ctx.globalAlpha = isTop ? (highlighted ? 1 : 0.5) : 0.95
      ctx.fillStyle = isTop ? '#FF9966' : '#FFFFFF'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillText(label, n.x, ly)
    }

    ctx.globalAlpha = 1
  }, [hoveredNode, isTopNode, isHighlighted])

  const nodeCanvasObjectMode = useCallback(() => 'replace' as const, [])

  // Draw year axis + swim lane backgrounds + community labels
  const onRenderFramePost = useCallback((ctx: CanvasRenderingContext2D) => {
    if (!fgRef.current) return
    const nodes = fgRef.current.graphData().nodes as GraphNodeInternal[]
    if (!nodes.length) return

    // Compute actual bounds from node positions
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
    nodes.forEach(n => {
      if (n.x === undefined || n.y === undefined) return
      if (n.x < minX) minX = n.x
      if (n.x > maxX) maxX = n.x
      if (n.y < minY) minY = n.y
      if (n.y > maxY) maxY = n.y
    })
    if (!isFinite(minX)) return

    const yPad = 40
    const { padding, usableWidth, yearSpan, halfW, halfH, laneHeight, communityYPositions } = layoutParams

    ctx.save()

    // Draw swim lane backgrounds (alternating subtle bands)
    if (layoutMode === 'timeline' && communityCount > 0) {
      for (let i = 0; i < communityCount; i++) {
        const laneTop = padding + i * laneHeight - halfH
        // Alternating subtle background
        if (i % 2 === 0) {
          ctx.fillStyle = 'rgba(255,255,255,0.015)'
          ctx.fillRect(minX - 40, laneTop, maxX - minX + 80, laneHeight)
        }
        // Lane separator line
        if (i > 0) {
          ctx.strokeStyle = 'rgba(255,255,255,0.06)'
          ctx.lineWidth = 0.5
          ctx.setLineDash([4, 4])
          ctx.beginPath()
          ctx.moveTo(minX - 40, laneTop)
          ctx.lineTo(maxX + 40, laneTop)
          ctx.stroke()
          ctx.setLineDash([])
        }
        // Lane label on left
        const cy = communityYPositions.get(i) ?? 0
        const label = communityNames[String(i)] ?? `Path ${i}`
        ctx.globalAlpha = 0.5
        ctx.font = '600 10px -apple-system, Helvetica, Arial, sans-serif'
        ctx.textAlign = 'right'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = COMMUNITY_COLORS[i % COMMUNITY_COLORS.length]
        ctx.fillText(label, minX - 50, cy)
      }
    }

    // Year axis — vertical lines at each year's target X position
    ctx.font = '11px -apple-system, Helvetica, Arial, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'

    for (let year = yearRange.min; year <= yearRange.max; year++) {
      const x = padding + ((year - yearRange.min) / yearSpan) * usableWidth - halfW
      // Vertical guide line
      ctx.strokeStyle = 'rgba(255,255,255,0.08)'
      ctx.lineWidth = 0.5
      ctx.beginPath()
      ctx.moveTo(x, minY - yPad)
      ctx.lineTo(x, maxY + yPad)
      ctx.stroke()
      // Year label at top
      ctx.globalAlpha = 0.6
      ctx.fillStyle = '#FFFFFF'
      ctx.fillText(String(year), x, minY - yPad - 18)
    }

    // Community labels on right side (for all communities)
    const centers = new Map<number, { sumY: number; count: number }>()
    nodes.forEach(n => {
      if (n.y === undefined) return
      const entry = centers.get(n.community) ?? { sumY: 0, count: 0 }
      entry.sumY += n.y
      entry.count++
      centers.set(n.community, entry)
    })

    ctx.textAlign = 'left'
    ctx.textBaseline = 'middle'
    ctx.globalAlpha = 0.7
    ctx.font = 'bold 12px -apple-system, Helvetica, Arial, sans-serif'

    centers.forEach((entry, communityId) => {
      const cy = entry.sumY / entry.count
      const label = communityNames[String(communityId)] ?? `Cluster ${communityId + 1}`
      ctx.fillStyle = COMMUNITY_COLORS[communityId % COMMUNITY_COLORS.length]
      ctx.fillText(label, maxX + 25, cy)
    })

    ctx.restore()
  }, [communityNames, layoutParams, yearRange, layoutMode, communityCount])

  const linkColor = useCallback((link: unknown) => {
    if (!hoveredNode) return 'rgba(255,255,255,0.12)'
    const l = link as { source: GraphNodeInternal; target: GraphNodeInternal }
    const srcId = typeof l.source === 'string' ? l.source : l.source?.id
    const tgtId = typeof l.target === 'string' ? l.target : l.target?.id
    if (srcId === hoveredNode || tgtId === hoveredNode) return 'rgba(255,255,255,0.5)'
    return 'rgba(255,255,255,0.03)'
  }, [hoveredNode])

  const handleNodeHover = useCallback((node: unknown) => {
    setHoveredNode((node as GraphNodeInternal | null)?.id ?? null)
  }, [])

  const handleNodeClick = useCallback((node: unknown) => {
    onNodeClick?.(node as GraphNode)
  }, [onNodeClick])

  const getNodeLabel = useCallback((node: unknown) => {
    const n = node as GraphNode
    return `${n.title}\n引用数: ${n.cited_by_count}\n年份: ${n.publication_year}`
  }, [])

  return (
    <div className={styles.graphContainer}>
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        width={width}
        height={height}
        backgroundColor={BG_COLOR}
        nodeCanvasObject={nodeCanvasObject}
        nodeCanvasObjectMode={nodeCanvasObjectMode}
        nodeLabel={getNodeLabel}
        nodeRelSize={4}
        linkColor={linkColor}
        linkWidth={1}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={0.75}
        linkDirectionalArrowColor={linkColor}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        onRenderFramePost={onRenderFramePost}
        cooldownTicks={layoutMode === 'cluster' ? 300 : 0}
        onEngineStop={() => fgRef.current?.zoomToFit(400, 60)}
        enableZoomInteraction={true}
        enableNodeDrag={true}
      />
    </div>
  )
}
