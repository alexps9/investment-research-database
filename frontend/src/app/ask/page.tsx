'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { AIStatus, SearchHit, AskResponse } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import { Badge } from '@/components/ui/Badge';
import { Sparkles, Search, Send, RefreshCw, AlertCircle } from 'lucide-react';

type Mode = 'search' | 'qa';

const typeBadge: Record<string, 'blue' | 'green' | 'purple' | 'default'> = {
  entity: 'blue', source: 'green', signal: 'purple',
};

function hitLink(hit: SearchHit): string | null {
  if (hit.object_type === 'entity') return `/wiki/entities/${hit.object_id}`;
  return null;
}

export default function AskPage() {
  const { t } = useLang();
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [mode, setMode] = useState<Mode>('qa');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reindexing, setReindexing] = useState(false);
  const [reindexMsg, setReindexMsg] = useState<string | null>(null);

  useEffect(() => {
    api.get<AIStatus>('/ai/status').then(setStatus).catch(() => setStatus(null));
  }, []);

  const enabled = status?.embeddings_enabled ?? false;
  const qaEnabled = status?.chat_enabled ?? false;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    setHits([]);
    try {
      if (mode === 'qa') {
        const res = await api.post<AskResponse>('/ai/ask', { question: query, top_k: 8 });
        setAnswer(res.answer);
        setHits(res.sources);
      } else {
        const res = await api.get<SearchHit[]>(`/ai/search?q=${encodeURIComponent(query)}&limit=20`);
        setHits(res);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleReindex() {
    setReindexing(true);
    setReindexMsg(null);
    try {
      const res = await api.post<{ indexed: Record<string, number> }>('/ai/reindex', {});
      const total = Object.values(res.indexed).reduce((a, b) => a + b, 0);
      setReindexMsg(`${t('ask.reindex_done')}: ${total}`);
    } catch (err) {
      setReindexMsg(String(err));
    } finally {
      setReindexing(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <div className="mb-2 flex items-center gap-2">
        <Sparkles className="text-blue-600" size={22} />
        <h1 className="text-2xl font-bold text-gray-900">{t('ask.title')}</h1>
      </div>
      <p className="mb-6 text-sm text-gray-500">{t('ask.subtitle')}</p>

      {!enabled && (
        <div className="mb-6 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span>{t('ask.disabled')}</span>
        </div>
      )}

      {/* mode toggle */}
      <div className="mb-3 flex items-center justify-between">
        <div className="inline-flex rounded-lg border border-gray-200 p-0.5 text-sm">
          <button
            onClick={() => setMode('qa')}
            disabled={!qaEnabled}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-medium transition-colors ${
              mode === 'qa' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-50'
            } disabled:opacity-40`}
          >
            <Sparkles size={14} /> {t('ask.mode.qa')}
          </button>
          <button
            onClick={() => setMode('search')}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-medium transition-colors ${
              mode === 'search' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-50'
            }`}
          >
            <Search size={14} /> {t('ask.mode.search')}
          </button>
        </div>

        <button
          onClick={handleReindex}
          disabled={!enabled || reindexing}
          title={t('ask.reindex_hint')}
          className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40"
        >
          <RefreshCw size={13} className={reindexing ? 'animate-spin' : ''} />
          {reindexing ? t('ask.reindexing') : t('ask.reindex')}
        </button>
      </div>
      {reindexMsg && <p className="mb-3 text-xs text-gray-500">{reindexMsg}</p>}

      {/* query box */}
      <form onSubmit={handleSubmit} className="mb-6 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={!enabled}
          placeholder={mode === 'qa' ? t('ask.placeholder.qa') : t('ask.placeholder.search')}
          className="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
        />
        <button
          type="submit"
          disabled={!enabled || loading || !query.trim()}
          className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-40"
        >
          <Send size={15} /> {t('ask.send')}
        </button>
      </form>

      {loading && (
        <p className="text-sm text-gray-400">{mode === 'qa' ? t('ask.thinking') : t('ask.searching')}</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* AI answer */}
      {answer && (
        <div className="mb-6 rounded-xl border border-blue-100 bg-blue-50/50 p-5">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-blue-700">
            <Sparkles size={13} /> {t('ask.answer')}
          </div>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">{answer}</div>
        </div>
      )}

      {/* hits / sources */}
      {hits.length > 0 && (
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            {mode === 'qa' ? t('ask.sources') : `${hits.length} ${t('ask.sources')}`}
          </h2>
          <ul className="space-y-2">
            {hits.map((hit) => {
              const link = hitLink(hit);
              const inner = (
                <div className="flex items-start justify-between gap-3 rounded-lg border border-gray-100 bg-white p-3 hover:border-blue-200 hover:shadow-sm">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant={typeBadge[hit.object_type] ?? 'default'}>{hit.object_type}</Badge>
                      <span className="truncate text-sm font-medium text-gray-900">{hit.name}</span>
                    </div>
                    {hit.description && (
                      <p className="mt-1 line-clamp-2 text-xs text-gray-500">{hit.description}</p>
                    )}
                  </div>
                  <span className="shrink-0 text-xs text-gray-400">{(hit.score * 100).toFixed(0)}%</span>
                </div>
              );
              return (
                <li key={`${hit.object_type}-${hit.object_id}`}>
                  {link ? <Link href={link}>{inner}</Link> : inner}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {!loading && !error && answer === null && hits.length === 0 && query && (
        <p className="text-sm text-gray-400">{t('ask.no_results')}</p>
      )}
    </div>
  );
}
