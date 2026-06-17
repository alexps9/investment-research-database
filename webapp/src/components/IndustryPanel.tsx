'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Radio, TrendingUp, Users, Banknote, Activity, ExternalLink } from 'lucide-react';
import type { IndustryData } from '@/lib/types';
import { wikiHref } from '@/lib/api';
import { useLang } from '@/lib/i18n';

function EmptyCard({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50/60 p-6 text-center text-sm text-gray-400">
      {text}
    </div>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Radio;
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <span className={`flex h-10 w-10 items-center justify-center rounded-lg ${tone}`}>
        <Icon className="h-5 w-5" />
      </span>
      <div>
        <p className="text-2xl font-semibold leading-none text-gray-900">{value}</p>
        <p className="mt-1 text-xs text-gray-500">{label}</p>
      </div>
    </div>
  );
}

export default function IndustryPanel({ industry }: { industry?: IndustryData | null }) {
  const { t } = useLang();
  const corePeople = industry?.core_people ?? [];
  const techSignals = industry?.tech_signals ?? [];
  const impact = industry?.impact_md?.trim();
  const personSignals = industry?.person_signals ?? [];
  const capital = industry?.capital ?? [];
  const funding = industry?.funding ?? [];

  const personLabel = (personId?: string, name?: string, fallbackWiki?: string) => {
    const wiki = fallbackWiki || (personId ? wikiHref(personId) : undefined);
    if (name && wiki) {
      return (
        <a href={wiki} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 hover:underline">
          {name}
        </a>
      );
    }
    return <span className="font-medium text-gray-800">{name || '—'}</span>;
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-12">
      {/* Overview */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile icon={Users} label={t('industry.talent')} value={corePeople.length} tone="bg-emerald-50 text-emerald-600" />
        <StatTile icon={Activity} label={t('industry.signals_live')} value={personSignals.length} tone="bg-blue-50 text-blue-600" />
        <StatTile icon={Radio} label={t('industry.signals')} value={techSignals.length} tone="bg-violet-50 text-violet-600" />
        <StatTile icon={Banknote} label={t('industry.capital')} value={capital.length + funding.length} tone="bg-amber-50 text-amber-600" />
      </div>

      {/* Real-time signals of core people (web-searched) */}
      <section>
        <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold text-gray-900">
          <Activity className="h-5 w-5 text-blue-600" /> {t('industry.signals_live')}
        </h2>
        <p className="mb-4 text-xs text-gray-400">基于网络搜索的核心人物近期动态</p>
        {personSignals.length ? (
          <div className="grid gap-3 md:grid-cols-2">
            {personSignals.map((s, i) => (
              <div key={i} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md">
                <div className="flex items-center justify-between gap-2">
                  {personLabel(s.person_id, s.person, s.wiki_url)}
                  {s.date && <span className="text-xs text-gray-400">{s.date}</span>}
                </div>
                <h3 className="mt-1.5 text-sm font-medium text-gray-900">
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 hover:underline">
                      {s.title} <ExternalLink className="inline h-3 w-3" />
                    </a>
                  ) : (
                    s.title
                  )}
                </h3>
                {s.summary && <p className="mt-1 text-sm leading-relaxed text-gray-600">{s.summary}</p>}
              </div>
            ))}
          </div>
        ) : (
          <EmptyCard text="暂未捕捉到核心人物的实时信号" />
        )}
      </section>

      {/* Core people (= key people, link to wiki) */}
      <section>
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900">
          <Users className="h-5 w-5 text-emerald-600" /> {t('industry.talent')}
        </h2>
        {corePeople.length ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {corePeople.map((p) => (
              <a
                key={p.id}
                href={p.wiki_url ? wikiHref(p.wiki_url) : wikiHref(p.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="group rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-emerald-300 hover:shadow-md"
              >
                <p className="font-medium text-gray-900 group-hover:text-emerald-700">
                  {p.name}
                  <ExternalLink className="ml-1 inline h-3 w-3 text-gray-300 group-hover:text-emerald-500" />
                </p>
                {p.org && <p className="mt-1 text-xs text-gray-500">{p.org}</p>}
              </a>
            ))}
          </div>
        ) : (
          <EmptyCard text="暂未识别到核心人物" />
        )}
      </section>

      {/* Tech signals + impact (interpreted from the report) */}
      <div className="grid gap-6 lg:grid-cols-5">
        <section className="lg:col-span-2">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900">
            <Radio className="h-5 w-5 text-violet-600" /> {t('industry.signals')}
          </h2>
          {techSignals.length ? (
            <div className="space-y-3">
              {techSignals.map((sig, i) => (
                <div key={i} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                  <h3 className="font-medium text-gray-900">{sig.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-gray-600">{sig.summary}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyCard text="暂无技术信号" />
          )}
        </section>

        <section className="lg:col-span-3">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900">
            <TrendingUp className="h-5 w-5 text-rose-600" /> {t('industry.impact')}
          </h2>
          {impact ? (
            <article className="prose prose-sm max-w-none rounded-xl border border-gray-200 bg-white p-6">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{impact}</ReactMarkdown>
            </article>
          ) : (
            <EmptyCard text="产业影响分析尚未生成" />
          )}
        </section>
      </div>

      {/* Capital + funding (web-searched, last month) */}
      <div className="grid gap-6 md:grid-cols-2">
        <section>
          <h2 className="mb-1 flex items-center gap-2 text-base font-semibold text-gray-900">
            <Banknote className="h-4 w-4 text-amber-600" /> {t('industry.capital')}
          </h2>
          <p className="mb-3 text-xs text-gray-400">核心人物近期的资本介入（优先最新）</p>
          {capital.length ? (
            <ul className="space-y-2">
              {capital.map((c, i) => (
                <li key={i} className="rounded-lg border border-amber-200 bg-amber-50/50 px-4 py-3 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    {personLabel(c.person_id, c.person, c.wiki_url)}
                    {c.date && <span className="text-xs text-gray-400">{c.date}</span>}
                  </div>
                  <p className="mt-1 text-gray-700">
                    {c.target}
                    {[c.round, c.amount].filter(Boolean).length > 0 && (
                      <span className="ml-1 text-gray-500">· {[c.round, c.amount].filter(Boolean).join(' · ')}</span>
                    )}
                  </p>
                  {c.investors && <p className="mt-0.5 text-xs text-gray-500">{c.investors}</p>}
                  {c.url && (
                    <a href={c.url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-block text-xs text-blue-600">
                      来源
                    </a>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyCard text="暂无资本介入事件" />
          )}
        </section>

        <section>
          <h2 className="mb-1 flex items-center gap-2 text-base font-semibold text-gray-900">
            <Banknote className="h-4 w-4 text-violet-600" /> {t('industry.funding')}
          </h2>
          <p className="mb-3 text-xs text-gray-400">核心人物近期的融资事件（优先最新）</p>
          {funding.length ? (
            <ul className="space-y-2">
              {funding.map((f, i) => (
                <li key={i} className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    {personLabel(f.person_id, f.person, f.wiki_url)}
                    {f.date && <span className="text-xs text-gray-400">{f.date}</span>}
                  </div>
                  <p className="mt-1 text-gray-700">
                    {f.company}
                    {[f.round, f.amount].filter(Boolean).length > 0 && (
                      <span className="ml-1 text-gray-500">· {[f.round, f.amount].filter(Boolean).join(' · ')}</span>
                    )}
                  </p>
                  {f.url && (
                    <a href={f.url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-block text-xs text-blue-600">
                      来源
                    </a>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyCard text="暂无融资事件" />
          )}
        </section>
      </div>
    </div>
  );
}
