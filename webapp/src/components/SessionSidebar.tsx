'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { MessageSquarePlus, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import type { ResearchSessionListItem } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import clsx from 'clsx';

export default function SessionSidebar({
  activeId,
  onNew,
}: {
  activeId?: string;
  onNew?: () => void;
}) {
  const { t } = useLang();
  const router = useRouter();
  const pathname = usePathname();
  const [sessions, setSessions] = useState<ResearchSessionListItem[]>([]);

  const load = useCallback(async () => {
    try {
      const rows = await api.get<ResearchSessionListItem[]>('/research/sessions?limit=50', {
        cache: false,
      });
      setSessions(rows);
    } catch {
      setSessions([]);
    }
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, 8000);
    return () => clearInterval(iv);
  }, [load, pathname]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('删除此会话？')) return;
    await api.delete(`/research/sessions/${id}`);
    if (activeId === id) router.push('/');
    load();
  };

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-gray-200 bg-gray-50">
      <div className="border-b border-gray-200 p-3">
        <button
          type="button"
          onClick={onNew ?? (() => router.push('/'))}
          className="flex w-full items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-800 shadow-sm hover:bg-gray-50"
        >
          <MessageSquarePlus className="h-4 w-4" />
          {t('sidebar.new')}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          {t('sidebar.history')}
        </p>
        {sessions.length === 0 ? (
          <p className="px-2 text-sm text-gray-400">{t('sidebar.empty')}</p>
        ) : (
          <ul className="space-y-1">
            {sessions.map((s) => (
              <li key={s.id}>
                <Link
                  href={`/s/${s.id}`}
                  className={clsx(
                    'group flex items-start gap-2 rounded-lg px-2 py-2 text-sm transition',
                    activeId === s.id
                      ? 'bg-blue-50 text-blue-900'
                      : 'text-gray-700 hover:bg-gray-100',
                  )}
                >
                  <div className="min-w-0 flex-1">
                    <p className="line-clamp-2 font-medium">{s.question}</p>
                    <p className="mt-0.5 text-xs text-gray-400">
                      {s.status === 'running'
                        ? `${t('status.running')} ${s.pct}%`
                        : s.status === 'done'
                          ? t('status.done')
                          : t('status.failed')}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => handleDelete(e, s.id)}
                    className="shrink-0 rounded p-1 opacity-0 hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
                    aria-label="delete"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
