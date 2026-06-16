'use client';
import React, { useState } from 'react';
import Image from 'next/image';
import { LogIn, Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { useLang } from '@/lib/i18n';

export default function LoginScreen() {
  const { login } = useAuth();
  const { t, lang, setLang } = useLang();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    setLoading(true);
    setError(null);
    try {
      await login(username.trim(), password);
    } catch {
      setError(t('auth.failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center">
          <Image src="/logo.png" alt="Aseed+ Lab" width={170} height={68} priority className="object-contain" />
          <p className="mt-3 text-sm text-gray-500">{t('auth.subtitle')}</p>
        </div>

        <form
          onSubmit={onSubmit}
          className="rounded-2xl border border-gray-100 bg-white/80 p-6 shadow-xl backdrop-blur"
        >
          <h1 className="mb-5 text-center text-lg font-semibold text-gray-800">
            {t('auth.title')}
          </h1>

          <label className="mb-1 block text-xs font-medium text-gray-600">{t('auth.username')}</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            autoComplete="username"
            className="mb-4 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder={t('auth.username')}
          />

          <label className="mb-1 block text-xs font-medium text-gray-600">{t('auth.password')}</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            className="mb-4 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder={t('auth.password')}
          />

          {error && (
            <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !username || !password}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <LogIn size={16} />}
            {loading ? t('auth.signing_in') : t('auth.sign_in')}
          </button>
        </form>

        <div className="mt-4 flex justify-center gap-3 text-xs text-gray-400">
          <button onClick={() => setLang('zh')} className={lang === 'zh' ? 'font-semibold text-blue-600' : 'hover:text-gray-600'}>中文</button>
          <span>·</span>
          <button onClick={() => setLang('en')} className={lang === 'en' ? 'font-semibold text-blue-600' : 'hover:text-gray-600'}>EN</button>
        </div>
      </div>
    </div>
  );
}
