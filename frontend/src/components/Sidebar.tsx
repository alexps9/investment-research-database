'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';
import clsx from 'clsx';
import {
  LayoutDashboard, Radio, Zap, Box, BookOpen, Network,
} from 'lucide-react';
import { useLang } from '@/lib/i18n';

const NAV_KEYS = [
  { href: '/dashboard', tKey: 'nav.dashboard', icon: LayoutDashboard },
  { href: '/sources',   tKey: 'nav.sources',   icon: Radio            },
  { href: '/signals',   tKey: 'nav.signals',   icon: Zap              },
  { href: '/entities',  tKey: 'nav.entities',  icon: Box              },
  { href: '/wiki',      tKey: 'nav.wiki',      icon: BookOpen         },
  { href: '/graph',     tKey: 'nav.graph',     icon: Network          },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { lang, setLang, t } = useLang();

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-gray-200 bg-gray-50">
      {/* Logo */}
      <div className="flex items-center justify-center px-4 py-4 border-b border-gray-100">
        <Link href="/dashboard">
          <Image
            src="/logo.png"
            alt="Aseed+ Lab"
            width={140}
            height={56}
            priority
            className="object-contain"
          />
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 px-3 pt-3">
        {NAV_KEYS.map(({ href, tKey, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/');
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <Icon size={16} />
              {t(tKey)}
            </Link>
          );
        })}
      </nav>

      {/* Language toggle */}
      <div className="px-3 pb-4 pt-2 border-t border-gray-100">
        <div className="flex items-center rounded-lg overflow-hidden border border-gray-200 text-xs font-medium">
          <button
            onClick={() => setLang('zh')}
            className={clsx(
              'flex-1 py-1.5 transition-colors',
              lang === 'zh'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-500 hover:bg-gray-50'
            )}
          >
            中文
          </button>
          <button
            onClick={() => setLang('en')}
            className={clsx(
              'flex-1 py-1.5 transition-colors',
              lang === 'en'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-500 hover:bg-gray-50'
            )}
          >
            EN
          </button>
        </div>
      </div>
    </aside>
  );
}
