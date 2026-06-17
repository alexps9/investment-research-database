'use client';

import { useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Search, GitBranch, Network, TrendingUp } from 'lucide-react';
import clsx from 'clsx';
import SessionSidebar from '@/components/SessionSidebar';
import ResearchProgress from '@/components/ResearchProgress';
import { api } from '@/lib/api';
import type { ResearchSession } from '@/lib/types';
import { useLang } from '@/lib/i18n';

const PHASE_MSG: Record<string, string> = {
  queued: '排队中，等待空闲资源…',
  brief: '正在理解问题、明确研究范围并撰写研究简报…',
  plan: '正在把问题拆解为可独立检索的研究子主题…',
  research: '正在检索知识库与网络，收集证据…',
  synthesis: '正在归纳技术路线类别、产业信号并综合撰写报告…',
  report: '正在撰写技术路线 / 核心人物 / 产业追踪三大板块…',
  done: '研究完成',
};

const EXAMPLE_QUESTIONS = [
  '世界模型的主流技术路线和重要的人是谁？',
  '具身智能 VLA 的代表性工作与核心团队有哪些？',
  '视频生成世界模型近两年的演进与产业落地情况',
];

export default function SearchHome() {
  const { t } = useLang();
  const router = useRouter();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [running, setRunning] = useState<ResearchSession | null>(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    return () => {
      cancelledRef.current = true;
    };
  }, []);

  const poll = async (id: string) => {
    try {
      const s = await api.get<ResearchSession>(`/research/sessions/${id}`, { cache: false });
      if (cancelledRef.current) return;
      setRunning(s);
      if (s.status === 'running') {
        setTimeout(() => poll(id), 3000);
      } else if (s.status === 'done') {
        router.push(`/?id=${id}`);
      } else if (s.status === 'failed') {
        setError(s.error || '研究失败，请重试。');
        setLoading(false);
        setRunning(null);
      }
    } catch {
      if (!cancelledRef.current) setTimeout(() => poll(id), 4000);
    }
  };

  const start = async (q: string) => {
    const text = q.trim();
    if (text.length < 3 || loading) return;
    setLoading(true);
    setError('');
    try {
      const session = await api.post<ResearchSession>('/research/sessions', {
        question: text,
        max_subtopics: 5,
        searches_per_topic: 2,
      });
      // Keep the search page; render live progress below the box instead of
      // navigating away. Redirect to the report once the run completes.
      setRunning(session);
      poll(session.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : '启动失败');
      setLoading(false);
    }
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    start(question);
  };

  const isRunning = !!running;
  const phase = running?.phase ?? null;
  const message = running ? PHASE_MSG[running.phase || ''] || '正在研究…' : null;

  return (
    <div className="flex h-screen bg-gradient-to-b from-white to-slate-50">
      <SessionSidebar />
      <main className="flex flex-1 flex-col overflow-y-auto px-6">
        <div
          className={clsx(
            'mx-auto w-full max-w-2xl text-center transition-all',
            isRunning ? 'pt-12' : 'flex min-h-full flex-col justify-center',
          )}
        >
          <div className="mb-6 flex justify-center">
            <Image
              src="/logo.png"
              alt="Aseed Lab"
              width={260}
              height={120}
              priority
              className={clsx('h-auto select-none transition-all', isRunning ? 'w-40' : 'w-56')}
            />
          </div>
          {!isRunning && <p className="text-gray-500">{t('app.tagline')}</p>}

          <form onSubmit={submit} className={isRunning ? 'mt-2' : 'mt-8'}>
            <div className="relative mx-auto flex max-w-xl items-center">
              <Search className="absolute left-5 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={t('home.placeholder')}
                className="w-full rounded-full border border-gray-200 bg-white py-4 pl-12 pr-28 text-base shadow-lg shadow-slate-200/60 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-500/15"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || question.trim().length < 3}
                className="absolute right-2 rounded-full bg-blue-600 px-6 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '研究中…' : t('home.search')}
              </button>
            </div>
            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
          </form>

          {isRunning ? (
            <div className="mb-12 mt-8">
              <ResearchProgress phase={phase} message={message} pct={running?.pct ?? 0} />
            </div>
          ) : (
            <>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setQuestion(q)}
                    disabled={loading}
                    className="rounded-full border border-gray-200 bg-white px-4 py-1.5 text-xs text-gray-600 transition hover:border-blue-300 hover:text-blue-700"
                  >
                    {q}
                  </button>
                ))}
              </div>

              <div className="mt-12 flex justify-center gap-8 text-sm text-gray-400">
                <span className="flex items-center gap-1.5">
                  <GitBranch className="h-4 w-4" /> {t('report.trajectory')}
                </span>
                <span className="flex items-center gap-1.5">
                  <Network className="h-4 w-4" /> {t('report.people')}
                </span>
                <span className="flex items-center gap-1.5">
                  <TrendingUp className="h-4 w-4" /> {t('report.industry')}
                </span>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
