'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { DashboardStats, Signal, PipelineRun } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { PageHeader } from '@/components/ui/PageHeader';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { useLang } from '@/lib/i18n';
import { LayoutDashboard, Radio, Zap, Layers, Network } from 'lucide-react';

const EMPTY_STATS: DashboardStats = {
  total_sources: 0, total_signals: 0, total_entities: 0, total_relations: 0,
};

const signalTypeBadge: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  paper: 'blue', blog: 'green', tweet: 'purple', model_release: 'yellow',
};
const runStatusBadge: Record<string, 'green' | 'red' | 'yellow' | 'default'> = {
  success: 'green', failed: 'red', partial_success: 'yellow', running: 'default',
};

export default function DashboardPage() {
  const { t } = useLang();
  const [stats, setStats] = useState<DashboardStats>(EMPTY_STATS);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<DashboardStats>('/dashboard/stats').catch(() => EMPTY_STATS),
      api.get<Signal[]>('/dashboard/latest-signals').catch(() => [] as Signal[]),
      api.get<PipelineRun[]>('/dashboard/latest-runs').catch(() => [] as PipelineRun[]),
    ]).then(([s, sig, r]) => {
      setStats(s);
      setSignals(sig);
      setRuns(r);
    }).finally(() => setLoading(false));
  }, []);

  const statCards = [
    { labelKey: 'dashboard.stats.sources',  value: stats.total_sources,   href: '/data?tab=sources',  color: 'text-blue-600',   icon: Radio,   bg: 'from-blue-500 to-sky-500'      },
    { labelKey: 'dashboard.stats.signals',  value: stats.total_signals,   href: '/data?tab=signals',  color: 'text-purple-600', icon: Zap,     bg: 'from-purple-500 to-fuchsia-500' },
    { labelKey: 'dashboard.stats.entities', value: stats.total_entities,  href: '/data?tab=entities', color: 'text-green-600',  icon: Layers,  bg: 'from-emerald-500 to-green-500'  },
    { labelKey: 'dashboard.stats.orgs',     value: stats.total_relations, href: '/graph',             color: 'text-orange-600', icon: Network, bg: 'from-orange-500 to-amber-500'   },
  ];

  return (
    <div className="p-8">
      <PageHeader icon={LayoutDashboard} title={t('dashboard.title')} />

      {loading ? (
        <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}><CardContent className="pt-4"><div className="h-10 animate-pulse rounded bg-gray-100" /></CardContent></Card>
          ))}
        </div>
      ) : (
        <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {statCards.map(({ labelKey, value, href, color, icon: Icon, bg }) => (
            <Link key={labelKey} href={href}>
              <Card className="group cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md">
                <CardContent className="flex items-center justify-between pt-4">
                  <div>
                    <p className="text-sm text-gray-500">{t(labelKey)}</p>
                    <p className={`mt-1 text-3xl font-bold ${color}`}>{value}</p>
                  </div>
                  <div className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${bg} text-white opacity-90 shadow-sm transition-transform group-hover:scale-105`}>
                    <Icon size={20} />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>{t('dashboard.recent_signals')}</CardTitle></CardHeader>
          <CardContent className="p-0">
            {signals.length === 0 ? (
              <p className="px-5 py-4 text-sm text-gray-400">{loading ? t('common.loading') : t('dashboard.no_signals')}</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {signals.map((sig) => (
                  <li key={sig.id} className="flex items-start gap-3 px-5 py-3">
                    <Badge variant={signalTypeBadge[sig.signal_type] ?? 'default'} className="mt-0.5 shrink-0">
                      {sig.signal_type}
                    </Badge>
                    <div className="min-w-0">
                      <a href={sig.url} target="_blank" rel="noreferrer"
                        className="block truncate text-sm font-medium text-gray-800 hover:text-blue-600">
                        {sig.title}
                      </a>
                      {sig.analysis?.tldr && (
                        <p className="truncate text-xs text-gray-500">{sig.analysis.tldr}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{t('dashboard.recent_runs')}</CardTitle></CardHeader>
          <CardContent className="p-0">
            {runs.length === 0 ? (
              <p className="px-5 py-4 text-sm text-gray-400">{loading ? t('common.loading') : t('dashboard.no_runs')}</p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {runs.map((run) => (
                  <li key={run.id} className="flex items-center justify-between px-5 py-3">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{run.run_type}</p>
                      <p className="text-xs text-gray-400">
                        {formatDistanceToNow(new Date(run.started_at), { addSuffix: true })}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={runStatusBadge[run.status] ?? 'default'}>{run.status}</Badge>
                      <span className="text-xs text-gray-400">{run.success_items}/{run.total_items}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
