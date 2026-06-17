'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import SessionSidebar from '@/components/SessionSidebar';
import PeopleGraph from '@/components/PeopleGraph';
import { api } from '@/lib/api';
import type { EntityRelation, ResearchSession } from '@/lib/types';
import { useLang } from '@/lib/i18n';

export default function PeoplePage() {
  const { t } = useLang();
  const params = useParams();
  const id = params.id as string;
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [relations, setRelations] = useState<EntityRelation[]>([]);

  useEffect(() => {
    api.get<ResearchSession>(`/research/sessions/${id}`, { cache: false }).then(setSession);
    api.get<EntityRelation[]>('/graph/relations?limit=5000').then(setRelations);
  }, [id]);

  return (
    <div className="flex h-screen">
      <SessionSidebar activeId={id} />
      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center gap-4 border-b border-gray-200 px-6 py-3">
          <Link href={`/s/${id}`} className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
            <ArrowLeft className="h-4 w-4" />
            {t('report.back')}
          </Link>
          <h1 className="text-lg font-semibold">{t('people.title')}</h1>
        </header>
        <div className="flex-1 p-6">
          <PeopleGraph relations={relations} scope={session?.scope} />
        </div>
      </main>
    </div>
  );
}
