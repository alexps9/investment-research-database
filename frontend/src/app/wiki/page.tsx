'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import type { SearchResults } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Link from 'next/link';
import { Search, ExternalLink } from 'lucide-react';

export default function WikiPage() {
  const [q, setQ] = useState('');
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true);
    try {
      const data = await api.get<SearchResults>(`/search?q=${encodeURIComponent(q)}`);
      setResults(data);
    } catch (err) { alert(String(err)); }
    finally { setLoading(false); }
  }

  const total = results ? results.entities.length + results.signals.length + results.sources.length : 0;

  return (
    <div className="p-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900">Wiki Search</h1>
      <p className="mb-6 text-sm text-gray-500">Search across entities, signals, and sources.</p>

      <form onSubmit={handleSearch} className="mb-8 flex gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Search for entities, papers, models…"
            className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-4 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button type="submit" disabled={loading}
          className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {results && (
        <div className="space-y-6">
          <p className="text-sm text-gray-500">{total} result{total !== 1 ? 's' : ''} for &quot;{q}&quot;</p>

          {results.entities.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Entities ({results.entities.length})</CardTitle></CardHeader>
              <CardContent className="p-0">
                <ul className="divide-y divide-gray-100">
                  {results.entities.map(ent => (
                    <li key={ent.id} className="flex items-center justify-between px-5 py-3">
                      <div>
                        <Link href={`/wiki/entities/${ent.id}`} className="font-medium text-gray-900 hover:text-blue-600 text-sm">
                          {ent.name}
                        </Link>
                        {ent.description && <p className="text-xs text-gray-500 truncate max-w-md">{ent.description}</p>}
                      </div>
                      <Badge variant="blue">{ent.entity_type}</Badge>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {results.signals.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Signals ({results.signals.length})</CardTitle></CardHeader>
              <CardContent className="p-0">
                <ul className="divide-y divide-gray-100">
                  {results.signals.map(sig => (
                    <li key={sig.id} className="flex items-center justify-between px-5 py-3">
                      <div>
                        <a href={sig.url} target="_blank" rel="noreferrer"
                          className="flex items-center gap-1 text-sm font-medium text-gray-900 hover:text-blue-600">
                          {sig.title} <ExternalLink size={12} />
                        </a>
                        {sig.analysis?.tldr && <p className="text-xs text-gray-500 truncate max-w-md">{sig.analysis.tldr}</p>}
                      </div>
                      <Badge>{sig.signal_type}</Badge>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {results.sources.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Sources ({results.sources.length})</CardTitle></CardHeader>
              <CardContent className="p-0">
                <ul className="divide-y divide-gray-100">
                  {results.sources.map(src => (
                    <li key={src.id} className="flex items-center justify-between px-5 py-3">
                      <div>
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

          {total === 0 && (
            <p className="text-center text-sm text-gray-400 py-12">No results found. Try a different query.</p>
          )}
        </div>
      )}
    </div>
  );
}
