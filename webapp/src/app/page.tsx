'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';
import SessionSidebar from '@/components/SessionSidebar';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

export default function HomePage() {
  const { t } = useLang();
  const router = useRouter();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (q.length < 3 || loading) return;
    setLoading(true);
    setError('');
    try {
      const session = await api.post<{ id: string }>('/research/sessions', {
        question: q,
        max_subtopics: 5,
        searches_per_topic: 2,
      });
      router.push(`/s/${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '启动失败');
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      <SessionSidebar />
      <main className="flex flex-1 flex-col items-center justify-center px-6">
        <div className="w-full max-w-2xl text-center">
          <h1 className="text-4xl font-semibold tracking-tight text-gray-900">
            {t('app.title')}
          </h1>
          <p className="mt-2 text-gray-500">{t('app.tagline')}</p>
          <form onSubmit={submit} className="mt-10">
            <div className="relative mx-auto flex max-w-xl items-center">
              <Search className="absolute left-4 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={t('home.placeholder')}
                className="w-full rounded-full border border-gray-200 bg-white py-4 pl-12 pr-28 text-base shadow-lg shadow-gray-200/50 outline-none ring-blue-500 focus:ring-2"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || question.trim().length < 3}
                className="absolute right-2 rounded-full bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '…' : t('home.search')}
              </button>
            </div>
            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
          </form>
        </div>
      </main>
    </div>
  );
}
