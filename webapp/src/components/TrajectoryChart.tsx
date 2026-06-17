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
  impact: number;
  highlighted: boolean;
}

const LANE_LABELS: Record<string, string> = {
  video_gen: '视频生成',
  rl_based: '强化学习',
  latent_space: '隐空间',
  vla: '策略 / VLA',
  other: '其他',
};

const REL_META: Record<string, { color: string; label: string }> = {
  BUILT_ON: { color: '#6366f1', label: '基于 / 继承' },
  RELATED_TO: { color: '#94a3b8', label: '相关' },
  COMPETES_WITH: { color: '#ef4444', label: '竞争 / 对比' },
};
const PAPER_REL_TYPES = new Set(Object.keys(REL_META));

export default function TrajectoryChart({
  papers,
  relations,
  scope,
}: {
  papers: Entity[];
  relations: EntityRelation[];
  scope?: ResearchScope | null;
}) {
  const highlightIds = useMemo(() => new Set(scope?.paper_ids ?? []), [scope?.paper_ids]);

  const nodes = useMemo<PaperNode[]>(() => {
    return papers
      .map((p) => {
        const m = p.metadata || {};
        return {
          id: p.id,
          name: (m.short_title as string) || p.name,
          year: Number(m.year) || 2020,
          quarter: Number(m.quarter) || 1,
          lane: (m.lane as string) || 'other',
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

  const [yMin, yMax] = useMemo(() => {
    if (!nodes.length) return [2019.5, 2026.5];
    const ys = nodes.map((n) => n.year);
    return [Math.min(...ys) - 0.5, Math.max(...ys) + 0.5];
  }, [nodes]);

  // Layout geometry.
  const laneH = 170;
  const bandH = 132;
  const padL = 130;
  const padR = 40;
  const padT = 30;
  const padB = 54;
  const width = 1180;
  const height = padT + lanes.length * laneH + padB;

  const laneTop = (lane: string) => padT + lanes.indexOf(lane) * laneH + (laneH - bandH) / 2;
  const xOf = (year: number, quarter: number) => {
    const t = year + (quarter - 1) / 4;
    const ratio = (t - yMin) / (yMax - yMin || 1);
    return padL + ratio * (width - padL - padR);
  };

  // Greedy vertical spread within each lane band to avoid overlapping stacks.
  const nodePos = useMemo(() => {
    const map: Record<string, { x: number; y: number }> = {};
    const MIN_DX = 44;
    const STEP = 26;
    for (const lane of lanes) {
      const top = laneTop(lane);
      const center = top + bandH / 2;
      const half = bandH / 2 - 14;
      const placed: { x: number; y: number }[] = [];
      const laneNodes = nodes
        .filter((n) => n.lane === lane)
        .sort((a, b) => xOf(a.year, a.quarter) - xOf(b.year, b.quarter));
      for (const n of laneNodes) {
        const x = xOf(n.year, n.quarter);
        let y = center;
        for (let k = 0; k < 12; k += 1) {
          const offset = (k % 2 === 0 ? 1 : -1) * Math.ceil(k / 2) * STEP;
          const cand = Math.max(top + 14, Math.min(top + bandH - 14, center + offset));
          const clash = placed.some((q) => Math.abs(q.x - x) < MIN_DX && Math.abs(q.y - cand) < STEP - 4);
          if (!clash) {
            y = cand;
            break;
          }
          y = cand;
        }
        placed.push({ x, y });
        map[n.id] = { x, y };
      }
    }
    return map;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, lanes, yMin, yMax]);

  const paperIdSet = useMemo(() => new Set(nodes.map((n) => n.id)), [nodes]);
  const edges = useMemo(
    () =>
      relations.filter(
        (r) =>
          PAPER_REL_TYPES.has(r.relation_type) &&
          paperIdSet.has(r.subject_entity_id) &&
          paperIdSet.has(r.object_entity_id),
      ),
    [relations, paperIdSet],
  );

  const radius = (impact: number, highlighted: boolean) =>
    (highlighted ? 11 : 6) + Math.min(6, Math.sqrt(impact) * 0.7);

  if (!nodes.length) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 bg-white p-10 text-center text-sm text-gray-400">
        暂无可展示的学术工作数据
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <svg width={width} height={height} className="min-w-full">
        {/* lane bands */}
        {lanes.map((lane) => {
          const top = laneTop(lane);
          return (
            <g key={lane}>
              <rect
                x={padL - 8}
                y={top}
                width={width - padL - padR + 8}
                height={bandH}
                fill={laneColor(lane)}
                opacity={0.1}
                rx={14}
              />
              <text x={14} y={top + bandH / 2} dominantBaseline="middle" className="fill-gray-700 text-xs font-semibold">
                {LANE_LABELS[lane] ?? lane}
              </text>
            </g>
          );
        })}

        {/* year grid */}
        {Array.from({ length: Math.ceil(yMax - yMin) + 1 }, (_, i) => Math.ceil(yMin) + i)
          .filter((yr) => yr >= yMin && yr <= yMax)
          .map((yr) => {
            const x = xOf(yr, 1);
            return (
              <g key={yr}>
                <line x1={x} y1={padT - 8} x2={x} y2={height - padB} stroke="#e5e7eb" strokeDasharray="4 4" />
                <text x={x} y={height - 18} textAnchor="middle" className="fill-gray-500 text-xs">
                  {yr}
                </text>
              </g>
            );
          })}

        <defs>
          <marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
            <path d="M0,0 L7,3.5 L0,7 Z" fill="#94a3b8" />
          </marker>
        </defs>

        {/* edges */}
        {edges.map((e) => {
          const a = nodePos[e.subject_entity_id];
          const b = nodePos[e.object_entity_id];
          if (!a || !b) return null;
          const meta = REL_META[e.relation_type];
          return (
            <path
              key={e.id}
              d={`M${a.x},${a.y} C${(a.x + b.x) / 2},${a.y} ${(a.x + b.x) / 2},${b.y} ${b.x},${b.y}`}
              fill="none"
              stroke={meta.color}
              strokeWidth={1.2}
              opacity={0.4}
              markerEnd="url(#arrow)"
            />
          );
        })}

        {/* nodes */}
        {nodes.map((n) => {
          const pos = nodePos[n.id];
          if (!pos) return null;
          const r = radius(n.impact, n.highlighted);
          const fill = laneColor(n.lane);
          const showLabel = n.highlighted || n.impact >= 3;
          return (
            <g key={n.id}>
              <circle
                cx={pos.x}
                cy={pos.y}
                r={r}
                fill={fill}
                fillOpacity={n.highlighted ? 0.95 : 0.5}
                stroke={n.highlighted ? '#1e40af' : '#fff'}
                strokeWidth={n.highlighted ? 2.5 : 1}
              />
              <title>{`${n.name} · ${n.year}`}</title>
              {showLabel && (
                <text
                  x={pos.x}
                  y={pos.y - r - 4}
                  textAnchor="middle"
                  className={n.highlighted ? 'fill-gray-900 text-[10px] font-semibold' : 'fill-gray-500 text-[10px]'}
                >
                  {n.name.length > 16 ? `${n.name.slice(0, 15)}…` : n.name}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-gray-500">
        {Object.values(REL_META).map((m) => (
          <span key={m.label} className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-5 rounded" style={{ backgroundColor: m.color }} />
            {m.label}
          </span>
        ))}
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-full border-2 border-blue-800 bg-amber-400" />
          研究相关论文（高亮）
        </span>
        <span className="text-gray-400">圆点大小 = 影响力</span>
      </div>
    </div>
  );
}
