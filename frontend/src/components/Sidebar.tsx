'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';
import clsx from 'clsx';
import {
  LayoutDashboard, Database, Sparkles, Network, Flame, TrendingUp, LogOut,
} from 'lucide-react';
import { useLang } from '@/lib/i18n';
import { useAuth } from '@/lib/auth';

const NAV_GROUPS = [
  {
    titleKey: 'nav.group.overview',
    items: [{ href: '/dashboard', tKey: 'nav.dashboard', icon: LayoutDashboard }],
  },
  {
    titleKey: 'nav.group.knowledge',
    items: [
      { href: '/data', tKey: 'nav.data', icon: Database },
      { href: '/explore', tKey: 'nav.explore', icon: Sparkles },
      { href: '/graph', tKey: 'nav.graph', icon: Network },
    ],
  },
  {
    titleKey: 'nav.group.insight',
    items: [
      { href: '/daily', tKey: 'nav.daily', icon: Flame },
      { href: '/funding', tKey: 'nav.funding', icon: TrendingUp },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { lang, setLang, t } = useLang();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-gray-200 bg-white">
      {/* Logo */}
      <div className="flex items-center justify-center border-b border-gray-100 px-4 py-5">
        <Link href="/dashboard">
          <Image src="/logo.png" alt="Aseed+ Lab" width={150} height={60} priority className="object-contain" />
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 pt-5">
        {NAV_GROUPS.map((group) => (
          <div key={group.titleKey}>
            <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
              {t(group.titleKey)}
            </p>
            <div className="space-y-0.5">
              {group.items.map(({ href, tKey, icon: Icon }) => {
                const active = pathname === href || pathname.startsWith(href + '/');
                return (
                  <Link
                    key={href}
                    href={href}
                    className={clsx(
                      'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all',
                      active
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                    )}
                  >
                    {active && <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-blue-600" />}
                    <Icon size={17} className={active ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'} />
                    {t(tKey)}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Language toggle */}
      <div className="border-t border-gray-100 px-3 pb-4 pt-3">
        <div className="flex items-center overflow-hidden rounded-lg border border-gray-200 text-xs font-medium">
          <button
            onClick={() => setLang('zh')}
            className={clsx('flex-1 py-1.5 transition-colors', lang === 'zh' ? 'bg-blue-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50')}
          >
            中文
          </button>
          <button
            onClick={() => setLang('en')}
            className={clsx('flex-1 py-1.5 transition-colors', lang === 'en' ? 'bg-blue-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50')}
          >
            EN
          </button>
        </div>

        {/* Current user + logout */}
        {user && (
          <div className="mt-3 flex items-center justify-between gap-2 rounded-lg bg-gray-50 px-3 py-2">
            <div className="flex min-w-0 items-center gap-2">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-600 text-[11px] font-semibold text-white">
                {(user.display_name || user.username).charAt(0).toUpperCase()}
              </span>
              <span className="truncate text-xs font-medium text-gray-700">
                {user.display_name || user.username}
              </span>
            </div>
            <button
              onClick={logout}
              title={t('auth.logout')}
              className="shrink-0 rounded-md p-1 text-gray-400 transition-colors hover:bg-gray-200 hover:text-gray-700"
            >
              <LogOut size={15} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
