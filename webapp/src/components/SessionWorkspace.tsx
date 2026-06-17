'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowLeft, FileDown, GitBranch, Network, TrendingUp } from 'lucide-react';
import SessionSidebar from '@/components/SessionSidebar';
import ResearchProgress from '@/components/ResearchProgress';
import TrajectoryChart from '@/components/TrajectoryChart';
import PeopleGraph from '@/components/PeopleGraph';
import IndustryPanel from '@/components/IndustryPanel';
import { api } from '@/lib/api';
import type { Entity, EntityRelation, ResearchSession } from '@/lib/types';
import { useLang } from '@/lib/i18n';

const PRINT_CSS = `
@media print {
  body * { visibility: hidden !important; }
  #research-report, #research-report * { visibility: visible !important; }
  #research-report { position: absolute; left: 0; top: 0; width: 100%; padding: 0 8mm; }
  .no-print { display: none !important; }
}`;

const PHASE_MSG: Record<string, string> = {
  queued: '排队中，等待空闲资源…',
  brief: '正在理解问题、明确研究范围并撰写研究简报…',
  plan: '正在把问题拆解为可独立检索的研究子主题…',
  research: '正在检索知识库与网络，收集证据…',
  synthesis: '正在归纳技术路线类别、产业信号并综合撰写报告…',
  report: '正在撰写技术路线 / 核心人物 / 产业追踪三大板块…',
  done: '研究完成',
};

function progressMsg(session: { phase?: string | null }): string {
  return PHASE_MSG[session.phase || ''] || '正在研究…';
}

const mdComponents = {
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => {
    const h = href || '';
    if (h.startsWith('/wiki/')) {
      return (
        <a href={h} className="text-blue-600 underline">
          {children}
        </a>
      );
    }
    return (
      <a href={h} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
        {children}
      </a>
    );
  },
};

type View = 'report' | 'trajectory' | 'people' | 'industry';

export default function SessionWorkspace({ id, view }: { id: string; view: View }) {
  const { t } = useLang();
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [error, setError] = useState('');

  // Sub-view datasets (lazy-loaded only when needed).
  const [papers, setPapers] = useState<Entity[]>([]);
  const [relations, setRelations] = useState<EntityRelation[]>([]);

  useEffect(() => {
    let cancelled = false;
    setSession(null);
    setError('');
    const poll = async () => {
      try {
        const s = await api.get<ResearchSession>(`/research/sessions/${id}`, { cache: false });
        if (cancelled) return;
        setSession(s);
        setError('');
        if (s.status === 'running') setTimeout(poll, 3000);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : '加载失败');
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (view === 'trajectory') {
      api.get<Entity[]>('/entities?entity_type=paper&limit=500').then(setPapers).catch(() => {});
      api.get<EntityRelation[]>('/graph/relations?limit=5000').then(setRelations).catch(() => {});
    } else if (view === 'people') {
      api.get<EntityRelation[]>('/graph/relations?limit=5000').then(setRelations).catch(() => {});
    }
  }, [view]);

  const link = (v: View) => (v === 'report' ? `/?id=${id}` : `/?id=${id}&view=${v}`);

  // ── Sub-view layouts ───────────────────────────────────────────────────────
  if (view !== 'report') {
    const titleKey =
      view === 'trajectory' ? 'trajectory.title' : view === 'people' ? 'people.title' : 'industry.title';
    return (
      <div className="flex h-screen">
        <SessionSidebar activeId={id} />
        <main className="flex flex-1 flex-col overflow-hidden">
          <header className="flex items-center gap-4 border-b border-slate-200 bg-white px-6 py-3">
            <Link
              href={link('report')}
              className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
            >
              <ArrowLeft className="h-4 w-4" />
              {t('report.back')}
            </Link>
            <h1 className="text-lg font-semibold">{t(titleKey)}</h1>
          </header>
          <div className="flex-1 overflow-auto p-6">
            {view === 'trajectory' && (
              <TrajectoryChart papers={papers} relations={relations} scope={session?.scope} />
            )}
            {view === 'people' && <PeopleGraph relations={relations} scope={session?.scope} />}
            {view === 'industry' && <IndustryPanel industry={session?.industry} />}
          </div>
        </main>
      </div>
    );
  }

  // ── Report / progress view ───────────────────────────────────────────────
  return (
    <div className="flex h-screen">
      <style>{PRINT_CSS}</style>
      <div className="no-print">
        <SessionSidebar activeId={id} />
      </div>
      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="no-print flex shrink-0 items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-3">
          <h1 className="truncate text-lg font-semibold text-slate-900">
            {session?.question ?? '…'}
          </h1>
          {session?.status === 'done' && (
            <div className="flex shrink-0 items-center gap-2">
              <Link
                href={link('trajectory')}
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm hover:bg-slate-50"
              >
                <GitBranch className="h-4 w-4" />
                {t('report.trajectory')}
              </Link>
              <Link
                href={link('people')}
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm hover:bg-slate-50"
              >
                <Network className="h-4 w-4" />
                {t('report.people')}
              </Link>
              <Link
                href={link('industry')}
                className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm hover:bg-slate-50"
              >
                <TrendingUp className="h-4 w-4" />
                {t('report.industry')}
              </Link>
              <button
                type="button"
                onClick={() => window.print()}
                className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
              >
                <FileDown className="h-4 w-4" />
                {t('report.export_pdf')}
              </button>
            </div>
          )}
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          {error && <p className="text-red-600">{error}</p>}
          {session?.status === 'running' && (
            <div className="no-print pt-6">
              <ResearchProgress
                phase={session.phase}
                message={progressMsg(session)}
                pct={session.pct}
              />
            </div>
          )}
          {session?.status === 'failed' && (
            <div className="mx-auto max-w-2xl rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
              {session.error || '研究失败，请重试。'}
            </div>
          )}
          {session?.status === 'done' && session.report && (
            <article id="research-report" className="prose prose-sm prose-blue mx-auto max-w-3xl">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                {session.report}
              </ReactMarkdown>
            </article>
          )}
        </div>
      </main>
    </div>
  );
}
