'use client';
import { useEffect, useState } from 'react';
import { Database, Zap, Layers, Radio } from 'lucide-react';
import { useLang } from '@/lib/i18n';
import { PageHeader } from '@/components/ui/PageHeader';
import { SourcesTab } from '@/components/data/SourcesTab';
import { SignalsTab } from '@/components/data/SignalsTab';
import { EntitiesTab } from '@/components/data/EntitiesTab';

type Tab = 'sources' | 'signals' | 'entities';

const TABS: { id: Tab; label: string; icon: typeof Radio }[] = [
  { id: 'sources',  label: '信号源',   icon: Radio  },
  { id: 'signals',  label: '信号',      icon: Zap    },
  { id: 'entities', label: '研究领域',  icon: Layers },
];

export default function DataPage() {
  const { t } = useLang();
  const [tab, setTab] = useState<Tab>('sources');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const initial = params.get('tab') as Tab | null;
    if (initial && TABS.some((t) => t.id === initial)) setTab(initial);
  }, []);

  function selectTab(next: Tab) {
    setTab(next);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', next);
    window.history.replaceState(null, '', url.toString());
  }

  return (
    <div className="p-8">
      <PageHeader icon={Database} title={t('data.title')} subtitle={t('data.subtitle')} />

      <div className="mb-6 inline-flex rounded-xl border border-gray-200 bg-white p-1 shadow-sm">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => selectTab(id)}
            className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              tab === id
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
            }`}
          >
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>

      <div className="animate-fade-in">
        {tab === 'sources'  && <SourcesTab />}
        {tab === 'signals'  && <SignalsTab />}
        {tab === 'entities' && <EntitiesTab />}
      </div>
    </div>
  );
}
