'use client';

import { useEffect, useRef, useState } from 'react';
import { Check, Loader2, Brain, Search, ListTree, Layers, FileText, TrendingUp } from 'lucide-react';
import clsx from 'clsx';

interface Stage {
  key: string;
  label: string;
  icon: typeof Brain;
  /** progress threshold at which this stage is considered started */
  at: number;
}

const STAGES: Stage[] = [
  { key: 'brief', label: '理解问题 · 撰写研究简报', icon: Brain, at: 5 },
  { key: 'plan', label: '拆解研究子主题', icon: ListTree, at: 15 },
  { key: 'research', label: '检索知识库与网络', icon: Search, at: 25 },
  { key: 'synthesis', label: '归纳路线类别 · 产业分析', icon: Layers, at: 78 },
  { key: 'report', label: '撰写报告与三大板块', icon: FileText, at: 90 },
  { key: 'done', label: '完成', icon: TrendingUp, at: 100 },
];

export default function ResearchProgress({
  phase,
  message,
  pct,
}: {
  phase?: string | null;
  message?: string | null;
  pct: number;
}) {
  // Keep a rolling log of distinct status messages so the user sees the agent "thinking".
  const [log, setLog] = useState<string[]>([]);
  const lastRef = useRef<string>('');

  useEffect(() => {
    const m = (message || '').trim();
    if (m && m !== lastRef.current) {
      lastRef.current = m;
      setLog((prev) => (prev[prev.length - 1] === m ? prev : [...prev, m]).slice(-8));
    }
  }, [message]);

  const currentIdx = STAGES.reduce(
    (acc, s, i) => (pct >= s.at ? i : acc),
    0,
  );

  return (
    <div className="mx-auto max-w-2xl">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        {/* Header */}
        <div className="flex items-center gap-3">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-blue-50">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-slate-900">深度研究进行中</p>
            <p className="truncate text-xs text-slate-500">{message || '正在准备…'}</p>
          </div>
          <span className="text-sm font-semibold tabular-nums text-blue-600">{pct}%</span>
        </div>

        {/* Progress bar */}
        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-700 ease-out"
            style={{ width: `${Math.max(3, pct)}%` }}
          />
        </div>

        {/* Stages */}
        <ol className="mt-6 space-y-3">
          {STAGES.map((s, i) => {
            const done = i < currentIdx || pct >= 100;
            const active = i === currentIdx && pct < 100;
            const Icon = s.icon;
            return (
              <li key={s.key} className="flex items-center gap-3">
                <span
                  className={clsx(
                    'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border transition',
                    done
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-600'
                      : active
                        ? 'border-blue-200 bg-blue-50 text-blue-600'
                        : 'border-slate-200 bg-white text-slate-300',
                  )}
                >
                  {done ? (
                    <Check className="h-4 w-4" />
                  ) : active ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </span>
                <span
                  className={clsx(
                    'text-sm transition',
                    done ? 'text-slate-500' : active ? 'font-medium text-slate-900' : 'text-slate-400',
                  )}
                >
                  {s.label}
                </span>
              </li>
            );
          })}
        </ol>
      </div>

      {/* Thinking log */}
      {log.length > 0 && (
        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            思考过程
          </p>
          <ul className="space-y-1.5">
            {log.map((m, i) => (
              <li
                key={`${i}-${m}`}
                className={clsx(
                  'flex items-start gap-2 text-xs',
                  i === log.length - 1 ? 'text-slate-700' : 'text-slate-400',
                )}
              >
                <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                <span className="leading-relaxed">{m}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-4 text-center text-xs text-slate-400">
        深度研究通常需要 2–5 分钟，可离开本页，稍后从左侧历史会话查看结果。
      </p>
    </div>
  );
}
