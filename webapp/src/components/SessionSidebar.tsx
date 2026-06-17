'use client';

import { useCallback, useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Plus, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import type { ResearchSessionListItem } from '@/lib/types';
import { useLang } from '@/lib/i18n';
import clsx from 'clsx';

function StatusDot({ status }: { status: string }) {
  const cls =
    status === 'running'
      ? 'bg-amber-400 animate-pulse'
      : status === 'done'
        ? 'bg-emerald-500'
        : 'bg-red-400';
  return <span className={clsx('inline-block h-1.5 w-1.5 shrink-0 rounded-full', cls)} />;
}

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
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-slate-200/80 bg-slate-50/80 backdrop-blur">
      <div className="flex items-center gap-2 px-4 py-4">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/logo.png" alt="Aseed Lab" width={120} height={36} className="h-8 w-auto" />
        </Link>
      </div>

      <div className="px-3 pb-3">
        <button
          type="button"
          onClick={onNew ?? (() => router.push('/'))}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-3 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          {t('sidebar.new')}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3">
        <p className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {t('sidebar.history')}
        </p>
        {sessions.length === 0 ? (
          <p className="px-3 py-6 text-center text-sm text-slate-400">{t('sidebar.empty')}</p>
        ) : (
          <ul className="space-y-0.5">
            {sessions.map((s) => (
              <li key={s.id}>
                <Link
                  href={`/s/${s.id}`}
                  className={clsx(
                    'group flex items-start gap-2.5 rounded-lg px-3 py-2.5 text-sm transition',
                    activeId === s.id
                      ? 'bg-white text-slate-900 shadow-sm ring-1 ring-slate-200'
                      : 'text-slate-600 hover:bg-white/70',
                  )}
                >
                  <span className="mt-1.5">
                    <StatusDot status={s.status} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="line-clamp-2 leading-snug">{s.question}</p>
                    <p className="mt-0.5 text-[11px] text-slate-400">
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
                    className="shrink-0 rounded-md p-1 text-slate-400 opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
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

      <div className="border-t border-slate-200/70 px-4 py-3 text-[11px] text-slate-400">
        Aseed Lab · Research Studio
      </div>
    </aside>
  );
}
