'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileDown, GitBranch, Network, TrendingUp } from 'lucide-react';
import SessionSidebar from '@/components/SessionSidebar';
import ResearchProgress from '@/components/ResearchProgress';
import { api } from '@/lib/api';
import type { ResearchSession } from '@/lib/types';
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

export default function SessionReportPage() {
  const { t } = useLang();
  const params = useParams();
  const id = params.id as string;
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const s = await api.get<ResearchSession>(`/research/sessions/${id}`, { cache: false });
        if (!cancelled) {
          setSession(s);
          setError('');
        }
        if (s.status === 'running' && !cancelled) {
          setTimeout(poll, 3000);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : '加载失败');
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const base = `/s/${id}`;

  return (
    <div className="flex h-screen">
      <style>{PRINT_CSS}</style>
      <div className="no-print">
        <SessionSidebar activeId={id} />
      </div>
      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="no-print flex shrink-0 items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
          <h1 className="truncate text-lg font-semibold text-gray-900">
            {session?.question ?? '…'}
          </h1>
          <div className="flex items-center gap-2">
            {session?.status === 'done' && (
              <>
                <Link
                  href={`${base}/trajectory`}
                  className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50"
                >
                  <GitBranch className="h-4 w-4" />
                  {t('report.trajectory')}
                </Link>
                <Link
                  href={`${base}/people`}
                  className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50"
                >
                  <Network className="h-4 w-4" />
                  {t('report.people')}
                </Link>
                <Link
                  href={`${base}/industry`}
                  className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-sm hover:bg-gray-50"
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
              </>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          {error && <p className="text-red-600">{error}</p>}
          {session?.status === 'running' && (
            <div className="no-print pt-6">
              <ResearchProgress
                phase={session.phase}
                message={session.phase === 'queued' ? '排队中，等待空闲资源…' : session.error || progressMsg(session)}
                pct={session.pct}
              />
            </div>
          )}
          {session?.status === 'failed' && (
            <p className="text-red-600">{session.error || '研究失败'}</p>
          )}
          {session?.status === 'done' && session.report && (
            <article
              id="research-report"
              className="prose prose-sm prose-blue mx-auto max-w-3xl"
            >
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
