'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { entityColor } from '@/lib/entityColors';

// Semantic color palette for relation types
const REL_COLORS: Record<string, string> = {
  WORKS_AT: '#3b82f6',      // blue
  PRE_WORKED_AT: '#93c5fd', // light blue
  FOCUSES_ON: '#10b981',    // green
  SUBTOPIC_OF: '#6366f1',   // indigo
  HAS_SUBTOPIC: '#818cf8',
  SUBSIDIARY_OF: '#f59e0b', // amber
  PARTNER_OF: '#14b8a6',
  COMPETITOR_OF: '#ef4444', // red
  ACQUIRED_BY: '#f97316',
  CO_AUTHOR: '#8b5cf6',     // violet
  ADVISOR_OF: '#ec4899',    // pink
  CLASSMATE: '#d946ef',
  CO_WORK: '#a855f7',
  SUBORDINATE_OF: '#94a3b8',
};

function relColor(label: string): string {
  return REL_COLORS[label] ?? '#94a3b8';
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  // mutated by the force engine at runtime
  x?: number;
  y?: number;
  __degree?: number;
}

export interface GraphLink {
  id?: string;
  source: string;
  target: string;
  label?: string;
}

interface Props {
  width: number;
  height: number;
  nodes: GraphNode[];
  links: GraphLink[];
  onSelect?: (node: GraphNode | null) => void;
  focusId?: string | null;
  /** smaller fonts / radii for embedded ego-graphs */
  compact?: boolean;
}

const endpointId = (e: unknown): string =>
  typeof e === 'object' && e !== null ? (e as GraphNode).id : (e as string);

export default function KnowledgeGraphCanvas({
  width,
  height,
  nodes,
  links,
  onSelect,
  focusId,
  compact = false,
}: Props) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null);
  const didFitRef = useRef(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoverId, setHoverId] = useState<string | null>(null);

  // Clone props into engine-owned objects (force-graph mutates x/y in place).
  const data = useMemo(() => {
    const degree: Record<string, number> = {};
    for (const l of links) {
      degree[l.source] = (degree[l.source] ?? 0) + 1;
      degree[l.target] = (degree[l.target] ?? 0) + 1;
    }
    return {
      nodes: nodes.map((n) => ({ ...n, __degree: degree[n.id] ?? 0 })),
      links: links.map((l) => ({ ...l })),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, links]);

  // adjacency for neighbor highlighting
  const neighbors = useMemo(() => {
    const map: Record<string, Set<string>> = {};
    for (const l of links) {
      (map[l.source] ??= new Set()).add(l.target);
      (map[l.target] ??= new Set()).add(l.source);
    }
    return map;
  }, [links]);

  const activeId = hoverId ?? selectedId;
  const highlightNodes = useMemo(() => {
    if (!activeId) return null;
    const s = new Set<string>([activeId]);
    neighbors[activeId]?.forEach((n) => s.add(n));
    return s;
  }, [activeId, neighbors]);

  const radius = useCallback(
    (n: GraphNode) => {
      const base = compact ? 4 : 5;
      return base + Math.sqrt(n.__degree ?? 0) * (compact ? 1.4 : 2.2);
    },
    [compact],
  );

  const paintNode = useCallback(
    (node: GraphNode, ctx: CanvasRenderingContext2D, scale: number) => {
      const r = radius(node);
      const dimmed = highlightNodes ? !highlightNodes.has(node.id) : false;
      const selected = node.id === activeId;

      ctx.save();
      ctx.globalAlpha = dimmed ? 0.18 : 1;

      if (selected) {
        ctx.beginPath();
        ctx.arc(node.x!, node.y!, r + 4, 0, 2 * Math.PI);
        ctx.fillStyle = `${entityColor(node.type)}33`;
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(node.x!, node.y!, r, 0, 2 * Math.PI);
      ctx.fillStyle = entityColor(node.type);
      ctx.fill();
      ctx.lineWidth = selected ? 2 : 1;
      ctx.strokeStyle = selected ? '#0f172a' : '#ffffff';
      ctx.stroke();

      // labels appear when zoomed in enough, or always for highlighted / selected nodes
      if (scale > 0.9 || selected || (highlightNodes && highlightNodes.has(node.id))) {
        const fontSize = (compact ? 3.2 : 3.6) + (selected ? 0.6 : 0);
        ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
        const label = node.name.length > 28 ? node.name.slice(0, 27) + '…' : node.name;
        const tw = ctx.measureText(label).width;
        ctx.fillStyle = 'rgba(255,255,255,0.82)';
        ctx.fillRect(node.x! - tw / 2 - 1, node.y! + r + 1, tw + 2, fontSize + 1.5);
        ctx.fillStyle = '#0f172a';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(label, node.x!, node.y! + r + 1.5);
      }
      ctx.restore();
    },
    [radius, highlightNodes, activeId, compact],
  );

  const paintPointerArea = useCallback(
    (node: GraphNode, color: string, ctx: CanvasRenderingContext2D) => {
      ctx.beginPath();
      ctx.arc(node.x!, node.y!, radius(node) + 2, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    },
    [radius],
  );

  // draw relation-type labels on edges when zoomed in
  const paintLinkLabel = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (link: any, ctx: CanvasRenderingContext2D, scale: number) => {
      if (!link.label || scale < 1.4) return;
      const s = link.source;
      const t = link.target;
      if (typeof s !== 'object' || typeof t !== 'object') return;
      const mx = (s.x + t.x) / 2;
      const my = (s.y + t.y) / 2;
      const fontSize = 2.6;
      ctx.save();
      ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
      const tw = ctx.measureText(link.label).width;
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.fillRect(mx - tw / 2 - 1, my - fontSize / 2 - 0.5, tw + 2, fontSize + 1);
      ctx.fillStyle = '#64748b';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(link.label, mx, my);
      ctx.restore();
    },
    [],
  );

  // zoom to fit once after the initial layout settles
  const handleEngineStop = useCallback(() => {
    if (didFitRef.current) return;
    didFitRef.current = true;
    fgRef.current?.zoomToFit(400, compact ? 30 : 70);
  }, [compact]);

  // re-fit when the dataset changes
  useEffect(() => {
    didFitRef.current = false;
  }, [data]);

  // external focus (search / deep link)
  useEffect(() => {
    if (!focusId || !fgRef.current) return;
    const node = data.nodes.find((n) => n.id === focusId);
    if (node && node.x != null) {
      fgRef.current.centerAt(node.x, node.y, 600);
      fgRef.current.zoom(4, 600);
      setSelectedId(focusId);
    }
  }, [focusId, data.nodes]);

  if (width <= 0 || height <= 0) return null;

  return (
    <ForceGraph2D
      ref={fgRef}
      width={width}
      height={height}
      graphData={data}
      backgroundColor="#f8fafc"
      nodeRelSize={1}
      nodeId="id"
      nodeLabel={(n: GraphNode) => `${n.name}  ·  ${n.type}`}
      nodeCanvasObject={paintNode}
      nodePointerAreaPaint={paintPointerArea}
      linkColor={(l: GraphLink) => {
        const active =
          highlightNodes &&
          highlightNodes.has(endpointId(l.source)) &&
          highlightNodes.has(endpointId(l.target));
        if (!active && highlightNodes) return 'rgba(148,163,184,0.15)';
        const base = relColor(l.label ?? '');
        return active ? base : `${base}55`;
      }}
      linkWidth={(l: GraphLink) =>
        highlightNodes &&
        highlightNodes.has(endpointId(l.source)) &&
        highlightNodes.has(endpointId(l.target))
          ? 1.8
          : 0.8
      }
      linkDirectionalArrowLength={compact ? 2.5 : 3.5}
      linkDirectionalArrowRelPos={1}
      linkDirectionalParticles={(l: GraphLink) =>
        highlightNodes &&
        highlightNodes.has(endpointId(l.source)) &&
        highlightNodes.has(endpointId(l.target))
          ? 2
          : 0
      }
      linkDirectionalParticleWidth={1.6}
      linkLabel={(l: GraphLink) => l.label ?? ''}
      linkCanvasObjectMode={() => 'after'}
      linkCanvasObject={paintLinkLabel}
      onNodeHover={(n: GraphNode | null) => setHoverId(n?.id ?? null)}
      onNodeClick={(n: GraphNode) => {
        setSelectedId(n.id);
        onSelect?.(n);
        if (n.x != null) fgRef.current?.centerAt(n.x, n.y, 500);
      }}
      onBackgroundClick={() => {
        setSelectedId(null);
        onSelect?.(null);
      }}
      cooldownTicks={120}
      onEngineStop={handleEngineStop}
    />
  );
}
