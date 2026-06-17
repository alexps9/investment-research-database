'use client';

import { useMemo } from 'react';
import type { Entity, EntityRelation, ResearchScope } from '@/lib/types';
import { laneColor } from '@/lib/entityColors';

interface PaperNode {
  id: string;
  name: string;
  year: number;
  quarter: number;
  lane: string;
  row: string;
  impact: number;
  highlighted: boolean;
}

const LANE_LABELS: Record<string, string> = {
  video_gen: 'Video-Generative',
  rl_based: 'RL-Based',
  latent_space: 'Latent-Space',
  vla: 'Policy / VLA',
};

const PAPER_REL_TYPES = new Set(['BUILT_ON', 'RELATED_TO', 'COMPETES_WITH']);

export default function TrajectoryChart({
  papers,
  relations,
  scope,
}: {
  papers: Entity[];
  relations: EntityRelation[];
  scope?: ResearchScope | null;
}) {
  const highlightIds = useMemo(
    () => new Set(scope?.paper_ids ?? []),
    [scope?.paper_ids],
  );

  const nodes = useMemo<PaperNode[]>(() => {
    return papers
      .map((p) => {
        const m = p.metadata || {};
        const year = Number(m.year) || 2020;
        const quarter = Number(m.quarter) || 1;
        return {
          id: p.id,
          name: (m.short_title as string) || p.name,
          year,
          quarter,
          lane: (m.lane as string) || 'other',
          row: (m.row as string) || '',
          impact: Number(m.impact_score) || 1,
          highlighted: highlightIds.has(p.id),
        };
      })
      .filter((n) => n.year >= 2018);
  }, [papers, highlightIds]);

  const lanes = useMemo(() => {
    const keys = Array.from(new Set(nodes.map((n) => n.lane)));
    const order = ['rl_based', 'video_gen', 'latent_space', 'vla', 'other'];
    return keys.sort((a, b) => order.indexOf(a) - order.indexOf(b));
  }, [nodes]);

  const years = useMemo(() => {
    if (!nodes.length) return [2020, 2026];
    const ys = nodes.map((n) => n.year);
    return [Math.min(...ys) - 0.5, Math.max(...ys) + 0.5];
  }, [nodes]);

  const [yMin, yMax] = years;
  const laneH = 120;
  const padL = 140;
  const padR = 40;
  const padT = 40;
  const padB = 50;
  const width = 1100;
  const height = padT + lanes.length * laneH + padB;

  const xOf = (year: number, quarter: number) => {
    const t = year + (quarter - 1) / 4;
    const ratio = (t - yMin) / (yMax - yMin);
    return padL + ratio * (width - padL - padR);
  };

  const yOf = (lane: string) => {
    const idx = lanes.indexOf(lane);
    return padT + idx * laneH + laneH / 2;
  };

  const nodePos = useMemo(() => {
    const map: Record<string, { x: number; y: number }> = {};
    for (const n of nodes) {
      map[n.id] = { x: xOf(n.year, n.quarter), y: yOf(n.lane) };
    }
    return map;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, lanes, yMin, yMax]);

  const paperIdSet = useMemo(() => new Set(nodes.map((n) => n.id)), [nodes]);

  const edges = useMemo(() => {
    return relations.filter(
      (r) =>
        PAPER_REL_TYPES.has(r.relation_type) &&
        paperIdSet.has(r.subject_entity_id) &&
        paperIdSet.has(r.object_entity_id),
    );
  }, [relations, paperIdSet]);

  const radius = (impact: number, highlighted: boolean) =>
    (highlighted ? 14 : 8) + Math.sqrt(impact) * 0.8;

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <svg width={width} height={height} className="min-w-full">
        {/* lane bands */}
        {lanes.map((lane, i) => (
          <g key={lane}>
            <rect
              x={padL}
              y={padT + i * laneH - laneH * 0.35}
              width={width - padL - padR}
              height={laneH * 0.7}
              fill={laneColor(lane)}
              opacity={0.08}
              rx={12}
            />
            <text
              x={12}
              y={padT + i * laneH + 4}
              className="fill-gray-700 text-xs font-semibold"
            >
              {LANE_LABELS[lane] ?? lane}
            </text>
          </g>
        ))}

        {/* year grid */}
        {Array.from({ length: Math.ceil(yMax - yMin) + 1 }, (_, i) => yMin + i).map((yr) => {
          const x = xOf(Math.floor(yr), 1);
          return (
            <g key={yr}>
              <line
                x1={x}
                y1={padT - 10}
                x2={x}
                y2={height - padB}
                stroke="#e5e7eb"
                strokeDasharray="4 4"
              />
              <text x={x} y={height - 16} textAnchor="middle" className="fill-gray-500 text-xs">
                {Math.round(yr)}
              </text>
            </g>
          );
        })}

        {/* edges */}
        {edges.map((e) => {
          const a = nodePos[e.subject_entity_id];
          const b = nodePos[e.object_entity_id];
          if (!a || !b) return null;
          const color =
            e.relation_type === 'BUILT_ON'
              ? '#6366f1'
              : e.relation_type === 'COMPETES_WITH'
                ? '#ef4444'
                : '#94a3b8';
          return (
            <line
              key={e.id}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={color}
              strokeWidth={1.2}
              opacity={0.45}
              markerEnd="url(#arrow)"
            />
          );
        })}

        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#94a3b8" />
          </marker>
        </defs>

        {/* nodes */}
        {nodes.map((n) => {
          const pos = nodePos[n.id];
          if (!pos) return null;
          const r = radius(n.impact, n.highlighted);
          const fill = laneColor(n.lane);
          return (
            <g key={n.id}>
              <circle
                cx={pos.x}
                cy={pos.y}
                r={r}
                fill={fill}
                fillOpacity={n.highlighted ? 0.95 : 0.55}
                stroke={n.highlighted ? '#1e40af' : '#fff'}
                strokeWidth={n.highlighted ? 2.5 : 1}
              />
              {r >= 10 && (
                <text
                  x={pos.x}
                  y={pos.y - r - 4}
                  textAnchor="middle"
                  className="fill-gray-800 text-[10px] font-medium"
                >
                  {n.name.length > 18 ? `${n.name.slice(0, 16)}…` : n.name}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded-full bg-indigo-500" /> BUILT_ON
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded-full bg-gray-400" /> RELATED_TO
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded-full bg-red-500" /> COMPETES_WITH
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-3 rounded-full border-2 border-blue-800 bg-amber-400" />{' '}
          研究相关论文
        </span>
      </div>
    </div>
  );
}
