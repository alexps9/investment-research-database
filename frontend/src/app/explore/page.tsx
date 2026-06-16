'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { AIStatus, SearchHit, AskResponse, SearchResults } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Sparkles, Search, Type, Send, RefreshCw, AlertCircle, BookOpen, ExternalLink } from 'lucide-react';

type Mode = 'qa' | 'semantic' | 'keyword';

const typeBadge: Record<string, 'blue' | 'green' | 'purple' | 'default'> = {
  entity: 'blue', source: 'green', signal: 'purple',
};

/** Entities deep-link to their Wiki; everything else is non-linked or external. */
function hitWikiLink(hit: SearchHit): string | null {
  return hit.object_type === 'entity' ? `/wiki/entities/${hit.object_id}` : null;
}

function HitRow({ hit }: { hit: SearchHit }) {
  const link = hitWikiLink(hit);
  const body = (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-gray-100 bg-white p-3.5 transition-all hover:border-blue-200 hover:shadow-sm">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Badge variant={typeBadge[hit.object_type] ?? 'default'}>{hit.object_type}</Badge>
          <span className="truncate text-sm font-medium text-gray-900">{hit.name}</span>
          {link && <BookOpen size={13} className="shrink-0 text-blue-400" />}
        </div>
        {hit.description && <p className="mt-1 line-clamp-2 text-xs text-gray-500">{hit.description}</p>}
      </div>
      <span className="shrink-0 rounded-full bg-gray-50 px-2 py-0.5 text-xs font-medium text-gray-400">
        {(hit.score * 100).toFixed(0)}%
      </span>
    </div>
  );
  return link ? <Link href={link} className="block">{body}</Link> : body;
}

export default function ExplorePage() {
  const { t } = useLang();
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [mode, setMode] = useState<Mode>('qa');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [keyword, setKeyword] = useState<SearchResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reindexing, setReindexing] = useState(false);
  const [reindexMsg, setReindexMsg] = useState<string | null>(null);

  useEffect(() => {
    api.get<AIStatus>('/ai/status').then(setStatus).catch(() => setStatus(null));
  }, []);

  const embeddingsOn = status?.embeddings_enabled ?? false;
  const qaOn = status?.chat_enabled ?? false;
  const needsAi = mode === 'qa' || mode === 'semantic';
  const disabled = needsAi && !embeddingsOn;

  function resetResults() {
    setAnswer(null);
    setHits([]);
    setKeyword(null);
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    resetResults();
    try {
      if (mode === 'qa') {
        const res = await api.post<AskResponse>('/ai/ask', { question: query, top_k: 8 });
        setAnswer(res.answer);
        setHits(res.sources);
      } else if (mode === 'semantic') {
        setHits(await api.get<SearchHit[]>(`/ai/search?q=${encodeURIComponent(query)}&limit=20`));
      } else {
        setKeyword(await api.get<SearchResults>(`/search?q=${encodeURIComponent(query)}`));
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

  const modes: { id: Mode; tKey: string; icon: typeof Search; on: boolean }[] = [
    { id: 'qa', tKey: 'explore.mode.qa', icon: Sparkles, on: qaOn },
    { id: 'semantic', tKey: 'explore.mode.semantic', icon: Search, on: embeddingsOn },
    { id: 'keyword', tKey: 'explore.mode.keyword', icon: Type, on: true },
  ];

  const placeholder =
    mode === 'qa' ? t('ask.placeholder.qa')
      : mode === 'semantic' ? t('ask.placeholder.search')
        : t('explore.placeholder.keyword');

  const keywordTotal = keyword ? keyword.entities.length + keyword.signals.length + keyword.sources.length : 0;

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader icon={Sparkles} title={t('explore.title')} subtitle={t('explore.subtitle')} />

      {disabled && (
        <div className="mb-5 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span>{t('ask.disabled')}</span>
        </div>
      )}

      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="inline-flex rounded-xl border border-gray-200 bg-white p-0.5 text-sm shadow-sm">
          {modes.map(({ id, tKey, icon: Icon, on }) => (
            <button
              key={id}
              onClick={() => { setMode(id); resetResults(); }}
              disabled={!on}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium transition-colors disabled:opacity-40 ${
                mode === id ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-500 hover:bg-gray-50'
              }`}
            >
              <Icon size={14} /> {t(tKey)}
            </button>
          ))}
        </div>

        {needsAi && (
          <button
            onClick={handleReindex}
            disabled={!embeddingsOn || reindexing}
            title={t('ask.reindex_hint')}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40"
          >
            <RefreshCw size={13} className={reindexing ? 'animate-spin' : ''} />
            {reindexing ? t('ask.reindexing') : t('ask.reindex')}
          </button>
        )}
      </div>
      {reindexMsg && <p className="mb-3 text-xs text-gray-500">{reindexMsg}</p>}

      <form onSubmit={handleSubmit} className="mb-6 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled}
          placeholder={placeholder}
          className="flex-1 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
        />
        <button
          type="submit"
          disabled={disabled || loading || !query.trim()}
          className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-40"
        >
          <Send size={15} /> {t('ask.send')}
        </button>
      </form>

      {loading && <p className="text-sm text-gray-400">{mode === 'qa' ? t('ask.thinking') : t('ask.searching')}</p>}
      {error && <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>}

      {answer && (
        <div className="animate-fade-in mb-6 rounded-xl border border-blue-100 bg-gradient-to-br from-blue-50/70 to-indigo-50/40 p-5">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-blue-700">
            <Sparkles size={13} /> {t('ask.answer')}
          </div>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">{answer}</div>
        </div>
      )}

      {/* Semantic / QA source hits */}
      {hits.length > 0 && (
        <div className="animate-fade-in">
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            {mode === 'qa' ? t('ask.sources') : `${hits.length} ${t('ask.sources')}`}
          </h2>
          <ul className="space-y-2">
            {hits.map((hit) => <li key={`${hit.object_type}-${hit.object_id}`}><HitRow hit={hit} /></li>)}
          </ul>
        </div>
      )}

      {/* Keyword grouped results */}
      {keyword && (
        <div className="animate-fade-in space-y-5">
          <p className="text-sm text-gray-500">{keywordTotal} {t('ask.sources')}</p>

          {keyword.entities.length > 0 && (
            <Card>
              <CardHeader><CardTitle>{t('data.tab.entities')} ({keyword.entities.length})</CardTitle></CardHeader>
              <CardContent className="p-0">
                <ul className="divide-y divide-gray-100">
                  {keyword.entities.map((ent) => (
                    <li key={ent.id} className="flex items-center justify-between px-5 py-3 hover:bg-blue-50/40">
                      <Link href={`/wiki/entities/${ent.id}`} className="group min-w-0">
                        <span className="flex items-center gap-1 text-sm font-medium text-gray-900 group-hover:text-blue-600">
                          {ent.name} <BookOpen size={12} className="text-blue-400" />
                        </span>
                        {ent.introduction && <p className="truncate text-xs text-gray-500">{ent.introduction}</p>}
                      </Link>
                      <Badge variant="blue">{ent.entity_type}</Badge>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {keyword.signals.length > 0 && (
            <Card>
              <CardHeader><CardTitle>{t('data.tab.signals')} ({keyword.signals.length})</CardTitle></CardHeader>
              <CardContent className="p-0">
                <ul className="divide-y divide-gray-100">
                  {keyword.signals.map((sig) => (
                    <li key={sig.id} className="flex items-center justify-between px-5 py-3 hover:bg-blue-50/40">
                      <a href={sig.url} target="_blank" rel="noreferrer" className="min-w-0">
                        <span className="flex items-center gap-1 text-sm font-medium text-gray-900 hover:text-blue-600">
                          {sig.title} <ExternalLink size={12} />
                        </span>
                        {sig.analysis?.tldr && <p className="truncate text-xs text-gray-500">{sig.analysis.tldr}</p>}
                      </a>
                      <Badge>{sig.signal_type}</Badge>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {keyword.sources.length > 0 && (
            <Card>
              <CardHeader><CardTitle>{t('data.tab.sources')} ({keyword.sources.length})</CardTitle></CardHeader>
              <CardContent className="p-0">
                <ul className="divide-y divide-gray-100">
                  {keyword.sources.map((src) => (
                    <li key={src.id} className="flex items-center justify-between px-5 py-3">
                      <div className="min-w-0">
                        <span className="text-sm font-medium text-gray-900">{src.name}</span>
                        {src.organization && <p className="text-xs text-gray-500">{src.organization.name}</p>}
                      </div>
                      <Badge>{src.source_type}</Badge>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {keywordTotal === 0 && <p className="py-12 text-center text-sm text-gray-400">{t('ask.no_results')}</p>}
        </div>
      )}

      {!loading && !error && answer === null && hits.length === 0 && keyword === null && query && (
        <p className="text-sm text-gray-400">{t('ask.no_results')}</p>
      )}
    </div>
  );
}
