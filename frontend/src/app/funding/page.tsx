'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { FundingEvent, FundingTrends } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Plus, Pencil, Trash2, ExternalLink, TrendingUp, List } from 'lucide-react';
import { format } from 'date-fns';
import { FundingEditModal } from '@/components/FundingEditModal';

type Tab = 'list' | 'trends';

function fmtAmount(v?: number) {
  if (v == null) return '—';
  return v.toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function Bars({ data, labelKey }: { data: { count: number; amount_usd: number }[]; labelKey: string }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <ul className="space-y-1.5">
      {data.map((d, i) => {
        const label = (d as unknown as Record<string, string>)[labelKey];
        return (
          <li key={i} className="flex items-center gap-3 text-xs">
            <span className="w-28 shrink-0 truncate text-gray-600" title={label}>{label}</span>
            <div className="flex-1">
              <div className="h-4 rounded bg-blue-500" style={{ width: `${(d.count / max) * 100}%`, minWidth: 6 }} />
            </div>
            <span className="w-10 shrink-0 text-right text-gray-500">{d.count}</span>
            <span className="w-20 shrink-0 text-right text-gray-400">{fmtAmount(d.amount_usd)}M</span>
          </li>
        );
      })}
      {data.length === 0 && <li className="text-gray-400">{/* empty */}—</li>}
    </ul>
  );
}

export default function FundingPage() {
  const { t } = useLang();
  const [tab, setTab] = useState<Tab>('list');
  const [events, setEvents] = useState<FundingEvent[]>([]);
  const [trends, setTrends] = useState<FundingTrends | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<FundingEvent | null>(null);

  async function load() {
    const [evs, tr] = await Promise.all([
      api.get<FundingEvent[]>('/funding?limit=300'),
      api.get<FundingTrends>('/funding/trends'),
    ]);
    setEvents(evs);
    setTrends(tr);
  }

  useEffect(() => {
    load().catch(console.error).finally(() => setLoading(false));
  }, []);

  function openCreate() { setEditing(null); setModalOpen(true); }
  function openEdit(f: FundingEvent) { setEditing(f); setModalOpen(true); }

  async function handleSaved() {
    await load();
  }

  async function handleDelete(f: FundingEvent) {
    if (!confirm(t('action.confirm_delete').replace('{name}', f.company_name))) return;
    try {
      await api.delete(`/funding/${f.id}`);
      await load();
    } catch (err) {
      alert(`${t('action.delete_failed')}: ${String(err)}`);
    }
  }

  const filtered = events.filter((e) =>
    !search || e.company_name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="p-8">
      <div className="mb-2 flex items-center gap-2">
        <TrendingUp className="text-blue-600" size={22} />
        <h1 className="text-2xl font-bold text-gray-900">{t('funding.title')}</h1>
      </div>
      <p className="mb-6 text-sm text-gray-500">{t('funding.subtitle')}</p>

      {/* tabs + actions */}
      <div className="mb-5 flex items-center justify-between">
        <div className="inline-flex rounded-lg border border-gray-200 p-0.5 text-sm">
          <button onClick={() => setTab('list')}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-medium transition-colors ${tab === 'list' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-50'}`}>
            <List size={14} /> {t('funding.tab.list')}
          </button>
          <button onClick={() => setTab('trends')}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-medium transition-colors ${tab === 'trends' ? 'bg-blue-600 text-white' : 'text-gray-500 hover:bg-gray-50'}`}>
            <TrendingUp size={14} /> {t('funding.tab.trends')}
          </button>
        </div>
        {tab === 'list' && (
          <button onClick={openCreate}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
            <Plus size={16} /> {t('funding.new')}
          </button>
        )}
      </div>

      {loading && <p className="text-sm text-gray-400">{t('common.loading')}</p>}

      {/* trends */}
      {!loading && tab === 'trends' && trends && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:max-w-md">
            <Card className="p-4">
              <div className="text-xs text-gray-500">{t('funding.stat.total_count')}</div>
              <div className="mt-1 text-2xl font-bold text-gray-900">{trends.total_count}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-gray-500">{t('funding.stat.total_amount')}</div>
              <div className="mt-1 text-2xl font-bold text-gray-900">{fmtAmount(trends.total_amount_usd)}</div>
            </Card>
          </div>
          <Card className="p-5">
            <h3 className="mb-3 text-sm font-semibold text-gray-700">{t('funding.trend.by_month')}</h3>
            <Bars data={trends.by_month} labelKey="month" />
          </Card>
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="p-5">
              <h3 className="mb-3 text-sm font-semibold text-gray-700">{t('funding.trend.by_round')}</h3>
              <Bars data={trends.by_round} labelKey="round" />
            </Card>
            <Card className="p-5">
              <h3 className="mb-3 text-sm font-semibold text-gray-700">{t('funding.trend.by_sector')}</h3>
              <Bars data={trends.by_sector} labelKey="sector" />
            </Card>
          </div>
        </div>
      )}

      {/* list */}
      {!loading && tab === 'list' && (
        <>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('funding.search')}
            className="mb-4 w-full max-w-xs rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="overflow-x-auto rounded-xl border border-gray-100">
            <table className="min-w-full divide-y divide-gray-100 text-sm">
              <thead className="bg-gray-50 text-left text-xs font-medium text-gray-500">
                <tr>
                  <th className="px-4 py-2.5">{t('funding.col.company')}</th>
                  <th className="px-4 py-2.5">{t('funding.col.round')}</th>
                  <th className="px-4 py-2.5">{t('funding.col.amount')}</th>
                  <th className="px-4 py-2.5">{t('funding.col.sector')}</th>
                  <th className="px-4 py-2.5">{t('funding.col.investors')}</th>
                  <th className="px-4 py-2.5">{t('funding.col.date')}</th>
                  <th className="px-4 py-2.5 text-right">{t('action.actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map((f) => (
                  <tr key={f.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-medium text-gray-900">
                      <span className="flex items-center gap-1">
                        {f.company_name}
                        {f.source_url && (
                          <a href={f.source_url} target="_blank" rel="noreferrer" className="text-gray-400 hover:text-blue-600">
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">{f.round ? <Badge variant="blue">{f.round}</Badge> : '—'}</td>
                    <td className="px-4 py-2.5 text-gray-700">{fmtAmount(f.amount_usd)}</td>
                    <td className="px-4 py-2.5 text-gray-600">{f.sector ?? '—'}</td>
                    <td className="px-4 py-2.5 text-gray-500">{f.investors?.length ? f.investors.join(', ') : '—'}</td>
                    <td className="px-4 py-2.5 text-gray-400">
                      {f.announced_at ? format(new Date(f.announced_at), 'yyyy-MM-dd') : '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => openEdit(f)}
                          className="rounded-md p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-600" title={t('action.edit')}>
                          <Pencil size={15} />
                        </button>
                        <button onClick={() => handleDelete(f)}
                          className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600" title={t('action.delete')}>
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <p className="py-12 text-center text-sm text-gray-400">{t('funding.empty')}</p>
            )}
          </div>
        </>
      )}

      <FundingEditModal
        open={modalOpen}
        funding={editing}
        onClose={() => setModalOpen(false)}
        onSaved={handleSaved}
      />
    </div>
  );
}
