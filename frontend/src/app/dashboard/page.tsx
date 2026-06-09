import { api } from '@/lib/api';
import type { DashboardStats, Signal, PipelineRun } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

async function getStats(): Promise<DashboardStats> {
  try { return await api.get<DashboardStats>('/dashboard/stats'); }
  catch { return { total_sources: 0, total_signals: 0, total_entities: 0, total_relations: 0 }; }
}
async function getLatestSignals(): Promise<Signal[]> {
  try { return await api.get<Signal[]>('/dashboard/latest-signals'); }
  catch { return []; }
}
async function getLatestRuns(): Promise<PipelineRun[]> {
  try { return await api.get<PipelineRun[]>('/dashboard/latest-runs'); }
  catch { return []; }
}

const signalTypeBadge: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  paper: 'blue', blog: 'green', tweet: 'purple', model_release: 'yellow',
};
const runStatusBadge: Record<string, 'green' | 'red' | 'yellow' | 'default'> = {
  success: 'green', failed: 'red', partial_success: 'yellow', running: 'default',
};

export default async function DashboardPage() {
  const [stats, signals, runs] = await Promise.all([getStats(), getLatestSignals(), getLatestRuns()]);

  const statCards = [
    { label: 'Sources', value: stats.total_sources, href: '/sources', color: 'text-blue-600' },
    { label: 'Signals', value: stats.total_signals, href: '/signals', color: 'text-purple-600' },
    { label: 'Entities', value: stats.total_entities, href: '/entities', color: 'text-green-600' },
    { label: 'Relations', value: stats.total_relations, href: '/graph', color: 'text-orange-600' },
  ];

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Dashboard</h1>

      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {statCards.map(({ label, value, href, color }) => (
          <Link key={label} href={href}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="pt-4">
                <p className="text-sm text-gray-500">{label}</p>
                <p className={`mt-1 text-3xl font-bold ${color}`}>{value}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Latest Signals</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {signals.length === 0 ? (
              <p className="px-5 py-4 text-sm text-gray-400">No signals yet.</p>
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
          <CardHeader>
            <CardTitle>Pipeline Runs</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {runs.length === 0 ? (
              <p className="px-5 py-4 text-sm text-gray-400">No runs yet.</p>
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
