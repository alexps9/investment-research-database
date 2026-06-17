'use client';

import { useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { Search, GitBranch, Network, TrendingUp } from 'lucide-react';
import SessionSidebar from '@/components/SessionSidebar';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

const EXAMPLE_QUESTIONS = [
  '世界模型的主流技术路线和重要的人是谁？',
  '具身智能 VLA 的代表性工作与核心团队有哪些？',
  '视频生成世界模型近两年的演进与产业落地情况',
];

export default function SearchHome() {
  const { t } = useLang();
  const router = useRouter();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const start = async (q: string) => {
    const text = q.trim();
    if (text.length < 3 || loading) return;
    setLoading(true);
    setError('');
    try {
      const session = await api.post<{ id: string }>('/research/sessions', {
        question: text,
        max_subtopics: 5,
        searches_per_topic: 2,
      });
      // Same route, query param → progress renders in place (static-export safe).
      router.push(`/?id=${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '启动失败');
      setLoading(false);
    }
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    start(question);
  };

  return (
    <div className="flex h-screen bg-gradient-to-b from-white to-slate-50">
      <SessionSidebar />
      <main className="flex flex-1 flex-col items-center justify-center px-6">
        <div className="w-full max-w-2xl text-center">
          <div className="mb-6 flex justify-center">
            <Image
              src="/logo.png"
              alt="Aseed Lab"
              width={260}
              height={120}
              priority
              className="h-auto w-56 select-none"
            />
          </div>
          <p className="text-gray-500">{t('app.tagline')}</p>

          <form onSubmit={submit} className="mt-8">
            <div className="relative mx-auto flex max-w-xl items-center">
              <Search className="absolute left-5 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={t('home.placeholder')}
                className="w-full rounded-full border border-gray-200 bg-white py-4 pl-12 pr-28 text-base shadow-lg shadow-slate-200/60 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-500/15"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || question.trim().length < 3}
                className="absolute right-2 rounded-full bg-blue-600 px-6 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '启动中…' : t('home.search')}
              </button>
            </div>
            {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
          </form>

          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {EXAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuestion(q)}
                disabled={loading}
                className="rounded-full border border-gray-200 bg-white px-4 py-1.5 text-xs text-gray-600 transition hover:border-blue-300 hover:text-blue-700"
              >
                {q}
              </button>
            ))}
          </div>

          <div className="mt-12 flex justify-center gap-8 text-sm text-gray-400">
            <span className="flex items-center gap-1.5">
              <GitBranch className="h-4 w-4" /> {t('report.trajectory')}
            </span>
            <span className="flex items-center gap-1.5">
              <Network className="h-4 w-4" /> {t('report.people')}
            </span>
            <span className="flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4" /> {t('report.industry')}
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}
