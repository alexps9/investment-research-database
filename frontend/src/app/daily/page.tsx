'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { DailyDigest } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import { Badge } from '@/components/ui/Badge';
import { Flame, RefreshCw, ExternalLink, Calendar } from 'lucide-react';

export default function DailyPage() {
  const { t } = useLang();
  const [current, setCurrent] = useState<DailyDigest | null>(null);
  const [history, setHistory] = useState<DailyDigest[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [windowDays, setWindowDays] = useState(1);
  const [error, setError] = useState<string | null>(null);

  async function loadHistory() {
    const list = await api.get<DailyDigest[]>('/daily?limit=60');
    setHistory(list);
    return list;
  }

  useEffect(() => {
    (async () => {
      try {
        const latest = await api.get<DailyDigest | null>('/daily/latest');
        setCurrent(latest);
        await loadHistory();
      } catch (err) {
        setError(String(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const digest = await api.post<DailyDigest>(
        `/daily/generate?window_days=${windowDays}`, {},
      );
      setCurrent(digest);
      await loadHistory();
    } catch (err) {
      setError(`${t('daily.generate_failed')}: ${err}`);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl p-8">
      <div className="mb-2 flex items-center gap-2">
        <Flame className="text-orange-500" size={22} />
        <h1 className="text-2xl font-bold text-gray-900">{t('daily.title')}</h1>
      </div>
      <p className="mb-6 text-sm text-gray-500">{t('daily.subtitle')}</p>

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-1.5 text-xs text-gray-500">
          {t('daily.window')}
          <input
            type="number"
            min={1}
            max={30}
            value={windowDays}
            onChange={(e) => setWindowDays(Math.max(1, Number(e.target.value) || 1))}
            className="w-16 rounded-lg border border-gray-200 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </label>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-1.5 rounded-lg bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600 disabled:opacity-40"
        >
          <RefreshCw size={14} className={generating ? 'animate-spin' : ''} />
          {generating ? t('daily.generating') : current ? t('daily.regenerate') : t('daily.generate')}
        </button>
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {loading && <p className="text-sm text-gray-400">{t('common.loading')}</p>}

      {!loading && !current && (
        <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-10 text-center text-sm text-gray-400">
          {t('daily.empty')}
        </div>
      )}

      {current && (
        <article className="mb-8 rounded-xl border border-orange-100 bg-orange-50/40 p-6">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-800">
              <Calendar size={15} className="text-orange-500" />
              {current.digest_date}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Badge variant="yellow">{t('daily.signal_count')}: {current.signal_count}</Badge>
              {current.model_name && <span>{t('daily.model')}: {current.model_name}</span>}
            </div>
          </div>

          {current.summary && (
            <div className="mb-5 whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
              {current.summary}
            </div>
          )}

          {current.highlights.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                {t('daily.highlights')}
              </h3>
              <ul className="space-y-2">
                {current.highlights.map((h, i) => (
                  <li key={h.signal_id ?? i} className="rounded-lg border border-gray-100 bg-white p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          {h.signal_type && <Badge variant="purple">{t(`signal_type.${h.signal_type}`)}</Badge>}
                          <span className="text-sm font-medium text-gray-900">{h.title}</span>
                        </div>
                        {h.reason && <p className="mt-1 text-xs text-gray-500">{h.reason}</p>}
                      </div>
                      {h.url && (
                        <a href={h.url} target="_blank" rel="noreferrer" className="shrink-0 text-gray-400 hover:text-blue-600">
                          <ExternalLink size={15} />
                        </a>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </article>
      )}

      {history.length > 1 && (
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
            {t('daily.history')}
          </h2>
          <ul className="divide-y divide-gray-100 rounded-xl border border-gray-100">
            {history.map((d) => (
              <li key={d.id}>
                <button
                  onClick={() => setCurrent(d)}
                  className={`flex w-full items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-gray-50 ${
                    current?.id === d.id ? 'bg-orange-50' : ''
                  }`}
                >
                  <span className="font-medium text-gray-700">{d.digest_date}</span>
                  <span className="text-xs text-gray-400">{d.signal_count} signals</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
