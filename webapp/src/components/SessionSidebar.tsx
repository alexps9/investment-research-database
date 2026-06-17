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

function relTime(iso: string): string {
  const d = new Date(iso).getTime();
  if (Number.isNaN(d)) return '';
  const diff = Date.now() - d;
  const m = Math.floor(diff / 60000);
  if (m < 1) return '刚刚';
  if (m < 60) return `${m} 分钟前`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h} 小时前`;
  const day = Math.floor(h / 24);
  if (day < 30) return `${day} 天前`;
  return new Date(iso).toLocaleDateString();
}

function groupOf(iso: string): string {
  const d = new Date(iso).getTime();
  if (Number.isNaN(d)) return '更早';
  const day = (Date.now() - d) / 86400000;
  if (day < 1) return '今天';
  if (day < 7) return '最近 7 天';
  if (day < 30) return '最近 30 天';
  return '更早';
}

const GROUP_ORDER = ['今天', '最近 7 天', '最近 30 天', '更早'];

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

  const grouped = GROUP_ORDER
    .map((g) => ({ group: g, items: sessions.filter((s) => groupOf(s.created_at) === g) }))
    .filter((x) => x.items.length > 0);

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-slate-200/70 bg-gradient-to-b from-slate-50 to-slate-100/70">
      <div className="flex items-center gap-2.5 px-4 pb-3 pt-5">
        <Link href="/" className="flex items-center gap-2.5">
          <Image src="/logo.png" alt="Aseed Lab" width={120} height={36} className="h-8 w-auto" />
          <span className="flex flex-col leading-none">
            <span className="text-sm font-semibold text-slate-800">Research Studio</span>
            <span className="mt-0.5 text-[10px] text-slate-400">深度研究工作台</span>
          </span>
        </Link>
      </div>

      <div className="px-3 pb-2">
        <button
          type="button"
          onClick={onNew ?? (() => router.push('/'))}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-3 py-2.5 text-sm font-medium text-white shadow-sm shadow-blue-500/20 transition hover:from-blue-700 hover:to-indigo-700 hover:shadow-blue-500/30"
        >
          <Plus className="h-4 w-4" />
          {t('sidebar.new')}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3">
        {sessions.length === 0 ? (
          <p className="px-3 py-10 text-center text-sm text-slate-400">{t('sidebar.empty')}</p>
        ) : (
          grouped.map(({ group, items }) => (
            <div key={group} className="mb-2">
              <p className="mb-1 px-3 pt-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                {group}
              </p>
              <ul className="space-y-0.5">
                {items.map((s) => (
                  <li key={s.id}>
                    <Link
                      href={`/?id=${s.id}`}
                      className={clsx(
                        'group flex items-start gap-2.5 rounded-lg px-3 py-2.5 text-sm transition',
                        activeId === s.id
                          ? 'bg-white text-slate-900 shadow-sm ring-1 ring-slate-200'
                          : 'text-slate-600 hover:bg-white/80',
                      )}
                    >
                      <span className="mt-1.5">
                        <StatusDot status={s.status} />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="line-clamp-2 leading-snug">{s.question}</p>
                        <p className="mt-1 flex items-center gap-1.5 text-[11px] text-slate-400">
                          <span>{relTime(s.created_at)}</span>
                          <span className="text-slate-300">·</span>
                          <span>
                            {s.status === 'running'
                              ? `${t('status.running')} ${s.pct}%`
                              : s.status === 'done'
                                ? t('status.done')
                                : t('status.failed')}
                          </span>
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
            </div>
          ))
        )}
      </div>

      <div className="border-t border-slate-200/70 px-4 py-3 text-[11px] text-slate-400">
        Aseed Lab · Research Studio
      </div>
    </aside>
  );
}
