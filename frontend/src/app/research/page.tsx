'use client';
import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';
import { PageHeader } from '@/components/ui/PageHeader';
import { Microscope, Send, Loader2, AlertCircle, Sparkles, FileText, Download, Database } from 'lucide-react';

interface Source { title: string; url: string }
interface KbSource {
  object_type: string;
  object_id: string;
  name: string;
  description?: string | null;
  score?: number | null;
  wiki_url?: string | null;
}
interface ResearchResult {
  question: string;
  brief: string;
  subtopics: string[];
  report: string;
  sources: Source[];
  kb_sources?: KbSource[];
}
interface ResearchJob {
  status: 'running' | 'done' | 'failed';
  phase: string;
  message: string;
  pct: number;
  question: string;
  result: ResearchResult | null;
  error: string | null;
}

const POLL_MS = 3000;
// The China-hosted backend is reachable through Vercel's edge but the cross-border
// hop occasionally drops a request (502 ROUTER_EXTERNAL_TARGET_CONNECTION_ERROR).
// A research run polls for minutes, so tolerate transient failures instead of
// aborting on the first one.
const MAX_POLL_FAILS = 8;
const START_RETRIES = 3;

// Print only the report container (browser "Save as PDF" — renders CJK natively
// and keeps selectable text + working links, unlike canvas-based exporters).
const PRINT_CSS = `
@media print {
  body * { visibility: hidden !important; }
  #research-report, #research-report * { visibility: visible !important; }
  #research-report { position: absolute; left: 0; top: 0; width: 100%; padding: 0 8mm; box-shadow: none !important; border: 0 !important; }
  .no-print { display: none !important; }
  a { color: #1d4ed8 !important; text-decoration: none; }
}`;

// Render internal wiki links in-app and external links in a new tab. `node` is
// react-markdown internal metadata and must not be forwarded to the DOM.
/* eslint-disable @typescript-eslint/no-explicit-any */
const mdComponents = {
  a: ({ node: _node, href, children, ...props }: any) => {
    const isExternal = !!href && /^https?:\/\//i.test(href);
    return (
      <a href={href} {...(isExternal ? { target: '_blank', rel: 'noreferrer' } : {})} {...props}>
        {children}
      </a>
    );
  },
};
/* eslint-enable @typescript-eslint/no-explicit-any */

async function withRetry<T>(fn: () => Promise<T>, retries: number): Promise<T> {
  let lastErr: unknown;
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (i < retries) await new Promise((r) => setTimeout(r, 1200 * (i + 1)));
    }
  }
  throw lastErr;
}

export default function ResearchPage() {
  const { t } = useLang();
  const [question, setQuestion] = useState('');
  const [maxSubtopics, setMaxSubtopics] = useState(5);
  const [searchesPerTopic, setSearchesPerTopic] = useState(2);
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const failsRef = useRef(0);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  function stopPolling() {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  }

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || running) return;
    setError(null);
    setJob(null);
    setRunning(true);
    failsRef.current = 0;
    try {
      const { job_id } = await withRetry(
        () => api.post<{ job_id: string }>('/research/start', {
          question: question.trim(),
          max_subtopics: maxSubtopics,
          searches_per_topic: searchesPerTopic,
        }),
        START_RETRIES,
      );
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.get<ResearchJob>(`/research/status/${job_id}`, { cache: false });
          failsRef.current = 0;
          setJob(status);
          if (status.status === 'done' || status.status === 'failed') {
            stopPolling();
            setRunning(false);
            if (status.status === 'failed') setError(status.error || '研究失败');
          }
        } catch (err) {
          // Tolerate transient cross-border edge failures; only give up after
          // several consecutive misses so the long-running job isn't dropped.
          failsRef.current += 1;
          if (failsRef.current >= MAX_POLL_FAILS) {
            stopPolling();
            setRunning(false);
            setError(`网络连接不稳定，已停止轮询：${String(err)}`);
          }
        }
      }, POLL_MS);
    } catch (err) {
      setRunning(false);
      setError(String(err));
    }
  }

  const result = job?.result ?? null;
  const pct = job?.pct ?? 0;

  return (
    <div className="mx-auto max-w-4xl p-8">
      <PageHeader icon={Microscope} title={t('research.title')} subtitle={t('research.subtitle')} />

      <form onSubmit={handleStart} className="mb-6 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={running}
          rows={3}
          placeholder={t('research.placeholder')}
          className="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
        />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
            <label className="flex items-center gap-1.5">
              {t('research.subtopics')}
              <select
                value={maxSubtopics}
                onChange={(e) => setMaxSubtopics(Number(e.target.value))}
                disabled={running}
                className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs"
              >
                {[2, 3, 4, 5, 6].map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
            <label className="flex items-center gap-1.5">
              {t('research.depth')}
              <select
                value={searchesPerTopic}
                onChange={(e) => setSearchesPerTopic(Number(e.target.value))}
                disabled={running}
                className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs"
              >
                {[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          </div>
          <button
            type="submit"
            disabled={running || !question.trim()}
            className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-40"
          >
            {running ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
            {running ? t('research.running') : t('research.start')}
          </button>
        </div>
      </form>

      {error && (
        <div className="mb-5 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span className="whitespace-pre-wrap">{error}</span>
        </div>
      )}

      {/* Progress */}
      {job && job.status === 'running' && (
        <div className="mb-6 rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50/70 to-indigo-50/40 p-5">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-blue-700">
            <Sparkles size={15} className="animate-pulse" /> {job.message}
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-blue-100">
            <div className="h-full rounded-full bg-blue-600 transition-all duration-500" style={{ width: `${pct}%` }} />
          </div>
          {result?.subtopics && result.subtopics.length > 0 && (
            <ul className="mt-3 space-y-1 text-xs text-gray-500">
              {result.subtopics.map((s, i) => <li key={i}>• {s}</li>)}
            </ul>
          )}
        </div>
      )}

      {/* Result */}
      {result && job?.status === 'done' && (
        <div className="animate-fade-in space-y-6">
          {result.subtopics?.length > 0 && (
            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
                <FileText size={13} /> {t('research.subtopics')}
              </h2>
              <ul className="grid gap-1.5 sm:grid-cols-2">
                {result.subtopics.map((s, i) => (
                  <li key={i} className="rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-600">{s}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={() => window.print()}
              className="no-print flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
              title={t('research.export_pdf')}
            >
              <Download size={15} /> {t('research.export_pdf')}
            </button>
          </div>

          {/* The printable report: body (exec summary + sections + conclusion) and
              the references block (DB sources w/ wiki links above external links)
              are produced by the agent and live inside result.report. */}
          <div id="research-report" className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <h1 className="mb-1 text-2xl font-bold text-gray-900">{result.question}</h1>
            <p className="mb-4 text-xs text-gray-400">{t('research.title')} · {new Date().toLocaleDateString()}</p>
            <div className="prose prose-sm prose-blue max-w-none prose-headings:font-bold prose-headings:text-gray-900 prose-a:text-blue-600 prose-h1:text-xl prose-h2:text-lg">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>{result.report}</ReactMarkdown>
            </div>
          </div>

          {/* Quick-access database sources that jump to their wiki entry. */}
          {result.kb_sources && result.kb_sources.length > 0 && (
            <div className="no-print rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
                <Database size={13} /> {t('research.kb_sources')} ({result.kb_sources.length})
              </h2>
              <div className="flex flex-wrap gap-2">
                {result.kb_sources.map((s, i) => (
                  s.wiki_url ? (
                    <a key={i} href={s.wiki_url}
                      className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs text-blue-700 hover:bg-blue-100">
                      {s.name}
                    </a>
                  ) : (
                    <span key={i} className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-500">
                      {s.name}
                    </span>
                  )
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      <style>{PRINT_CSS}</style>
    </div>
  );
}
