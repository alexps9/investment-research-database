'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Radio, TrendingUp, Users, Banknote, Newspaper, Activity } from 'lucide-react';
import type { FundingEvent, IndustryData, Signal } from '@/lib/types';
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

export default function IndustryPanel({
  industry,
  funding,
  signals,
}: {
  industry?: IndustryData | null;
  funding: FundingEvent[];
  signals: Signal[];
}) {
  const { t } = useLang();
  const techSignals = industry?.tech_signals ?? [];
  const topPeople = industry?.top_people ?? [];
  const capital = industry?.capital ?? [];
  const impact = industry?.impact_md?.trim();

  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-12">
      {/* Overview */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile icon={Radio} label={t('industry.signals')} value={techSignals.length} tone="bg-blue-50 text-blue-600" />
        <StatTile icon={Users} label={t('industry.talent')} value={topPeople.length} tone="bg-emerald-50 text-emerald-600" />
        <StatTile icon={Banknote} label={t('industry.capital')} value={capital.length} tone="bg-amber-50 text-amber-600" />
        <StatTile icon={Newspaper} label={t('industry.funding')} value={funding.length} tone="bg-violet-50 text-violet-600" />
      </div>

      {/* Tech signals */}
      <section>
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900">
          <Radio className="h-5 w-5 text-blue-600" /> {t('industry.signals')}
        </h2>
        {techSignals.length ? (
          <div className="grid gap-4 md:grid-cols-2">
            {techSignals.map((sig, i) => (
              <div key={i} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md">
                <h3 className="font-medium text-gray-900">
                  {sig.url ? (
                    <a href={sig.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {sig.title}
                    </a>
                  ) : (
                    sig.title
                  )}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">{sig.summary}</p>
              </div>
            ))}
          </div>
        ) : (
          <EmptyCard text="本方向暂未捕捉到明确的技术信号" />
        )}
      </section>

      {/* Impact + talent side by side to reduce whitespace */}
      <div className="grid gap-6 lg:grid-cols-5">
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

        <section className="lg:col-span-2">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900">
            <Users className="h-5 w-5 text-emerald-600" /> {t('industry.talent')}
          </h2>
          {topPeople.length ? (
            <div className="space-y-3">
              {topPeople.map((p, i) => (
                <div key={i} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                  <p className="font-medium text-gray-900">
                    {p.url ? (
                      <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        {p.name}
                      </a>
                    ) : (
                      p.name
                    )}
                    {p.org && <span className="ml-2 text-xs font-normal text-gray-500">{p.org}</span>}
                  </p>
                  {p.why && <p className="mt-1.5 text-sm leading-relaxed text-gray-600">{p.why}</p>}
                </div>
              ))}
            </div>
          ) : (
            <EmptyCard text="暂未识别到关键人物" />
          )}
        </section>
      </div>

      {/* Capital */}
      <section>
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900">
          <Banknote className="h-5 w-5 text-amber-600" /> {t('industry.capital')}
        </h2>
        {capital.length ? (
          <div className="grid gap-4 md:grid-cols-3">
            {capital.map((c, i) => (
              <div key={i} className="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
                <p className="font-medium text-gray-900">
                  {c.url ? (
                    <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {c.target}
                    </a>
                  ) : (
                    c.target
                  )}
                </p>
                <p className="mt-1 text-sm text-gray-600">
                  {[c.round, c.amount].filter(Boolean).join(' · ') || '融资信息'}
                </p>
                {c.investors && <p className="mt-1 text-xs text-gray-500">{c.investors}</p>}
              </div>
            ))}
          </div>
        ) : (
          <EmptyCard text="暂未发现明确的资本介入信息" />
        )}
      </section>

      {/* Live feeds: funding + signals in two columns */}
      <div className="grid gap-6 md:grid-cols-2">
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
            <Banknote className="h-4 w-4 text-violet-600" /> {t('industry.funding')}
          </h2>
          {funding.length ? (
            <ul className="space-y-2">
              {funding.slice(0, 12).map((f) => (
                <li key={f.id} className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm">
                  <span className="font-medium">{f.company_name}</span>
                  {f.round && <span className="ml-2 text-gray-500">{f.round}</span>}
                  {f.amount_raw && <span className="ml-2 text-amber-700">{f.amount_raw}</span>}
                  {f.source_url && (
                    <a href={f.source_url} target="_blank" rel="noopener noreferrer" className="ml-2 text-blue-600">
                      来源
                    </a>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyCard text="暂无相关融资记录" />
          )}
        </section>

        <section>
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900">
            <Activity className="h-4 w-4 text-blue-600" /> {t('industry.signals_live')}
          </h2>
          {signals.length ? (
            <ul className="space-y-2">
              {signals.slice(0, 12).map((s) => (
                <li key={s.id} className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm">
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 hover:underline">
                      {s.title}
                    </a>
                  ) : (
                    <span className="font-medium">{s.title}</span>
                  )}
                  {s.published_at && <span className="ml-2 text-xs text-gray-400">{s.published_at.slice(0, 10)}</span>}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyCard text="暂无实时信号" />
          )}
        </section>
      </div>
    </div>
  );
}
