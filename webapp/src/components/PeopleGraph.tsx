'use client';

import dynamic from 'next/dynamic';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { EntityRelation, ResearchScope } from '@/lib/types';
import { entityColor } from '@/lib/entityColors';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

interface GraphNode {
  id: string;
  name: string;
  type: string;
  highlighted: boolean;
}

interface GraphLink {
  source: string;
  target: string;
  label: string;
}

export default function PeopleGraph({
  relations,
  scope,
}: {
  relations: EntityRelation[];
  scope?: ResearchScope | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 800, h: 560 });

  const highlightIds = useMemo(() => {
    const s = new Set<string>();
    for (const id of scope?.topic_ids ?? []) s.add(id);
    for (const id of scope?.lane_ids ?? []) s.add(id);
    for (const id of scope?.paper_ids ?? []) s.add(id);
    for (const id of scope?.person_ids ?? []) s.add(id);
    for (const id of scope?.org_ids ?? []) s.add(id);
    return s;
  }, [scope]);

  const { nodes, links } = useMemo(() => {
    const nodeMap = new Map<string, GraphNode>();
    const linkList: GraphLink[] = [];
    const focusTypes = new Set(['person', 'organization', 'paper', 'topic']);
    const focusRels = new Set([
      'AUTHORED', 'FOCUSES_ON', 'WORKS_AT', 'SUBTOPIC_OF', 'BUILT_ON', 'RELATED_TO',
      'CO_AUTHOR', 'CO_WORK', 'FOCUSES_ON',
    ]);

    for (const r of relations) {
      if (!focusRels.has(r.relation_type)) continue;
      const subj = r.subject;
      const obj = r.object_entity;
      if (!subj || !obj) continue;
      if (!focusTypes.has(subj.entity_type) || !focusTypes.has(obj.entity_type)) continue;

      if (!nodeMap.has(subj.id)) {
        nodeMap.set(subj.id, {
          id: subj.id,
          name: subj.name,
          type: subj.entity_type,
          highlighted: highlightIds.has(subj.id),
        });
      }
      if (!nodeMap.has(obj.id)) {
        nodeMap.set(obj.id, {
          id: obj.id,
          name: obj.name,
          type: obj.entity_type,
          highlighted: highlightIds.has(obj.id),
        });
      }
      linkList.push({
        source: subj.id,
        target: obj.id,
        label: r.relation_type,
      });
    }

    // Keep nodes that are highlighted or connected to highlighted
    const connected = new Set<string>();
    for (const l of linkList) {
      if (highlightIds.has(l.source) || highlightIds.has(l.target)) {
        connected.add(l.source);
        connected.add(l.target);
      }
    }
    const filteredNodes = Array.from(nodeMap.values()).filter(
      (n) => n.highlighted || connected.has(n.id),
    );
    const keep = new Set(filteredNodes.map((n) => n.id));
    const filteredLinks = linkList.filter((l) => keep.has(l.source) && keep.has(l.target));

    return { nodes: filteredNodes.slice(0, 200), links: filteredLinks.slice(0, 400) };
  }, [relations, highlightIds]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setSize({ w: el.clientWidth, h: el.clientHeight });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="h-[calc(100vh-12rem)] min-h-[480px] w-full rounded-xl border border-gray-200 bg-gray-50">
      {nodes.length > 0 ? (
        <ForceGraph2D
          width={size.w}
          height={size.h}
          graphData={{ nodes, links }}
          nodeLabel="name"
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const n = node as GraphNode & { x?: number; y?: number };
            const r = n.highlighted ? 8 : 5;
            const dim = !n.highlighted;
            ctx.globalAlpha = dim ? 0.22 : 1;
            ctx.beginPath();
            ctx.arc(n.x ?? 0, n.y ?? 0, r, 0, 2 * Math.PI);
            ctx.fillStyle = entityColor(n.type);
            ctx.fill();
            if (n.highlighted) {
              ctx.strokeStyle = '#1e40af';
              ctx.lineWidth = 2 / globalScale;
              ctx.stroke();
            }
            if (globalScale > 0.8 || n.highlighted) {
              ctx.globalAlpha = dim ? 0.35 : 1;
              ctx.font = `${10 / globalScale}px sans-serif`;
              ctx.fillStyle = '#111';
              ctx.fillText(n.name.slice(0, 24), (n.x ?? 0) + r + 2, (n.y ?? 0) + 3);
            }
            ctx.globalAlpha = 1;
          }}
          linkColor={() => 'rgba(100,116,139,0.35)'}
        />
      ) : (
        <div className="flex h-full items-center justify-center text-gray-400">暂无图谱数据</div>
      )}
    </div>
  );
}
