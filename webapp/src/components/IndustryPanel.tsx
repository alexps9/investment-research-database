'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { FundingEvent, IndustryData, Signal } from '@/lib/types';
import { useLang } from '@/lib/i18n';

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
  if (!industry) {
    return <p className="text-gray-500">产业分析数据尚未生成</p>;
  }

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">{t('industry.signals')}</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {(industry.tech_signals ?? []).map((sig, i) => (
            <div key={i} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <h3 className="font-medium text-gray-900">
                {sig.url ? (
                  <a href={sig.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {sig.title}
                  </a>
                ) : (
                  sig.title
                )}
              </h3>
              <p className="mt-2 text-sm text-gray-600">{sig.summary}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">{t('industry.impact')}</h2>
        <article className="prose prose-sm max-w-none rounded-xl border border-gray-200 bg-white p-6">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{industry.impact_md || '—'}</ReactMarkdown>
        </article>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">{t('industry.talent')}</h2>
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500">
              <tr>
                <th className="px-4 py-2">姓名</th>
                <th className="px-4 py-2">机构</th>
                <th className="px-4 py-2">说明</th>
              </tr>
            </thead>
            <tbody>
              {(industry.top_people ?? []).map((p, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-medium">
                    {p.url ? (
                      <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-blue-600">
                        {p.name}
                      </a>
                    ) : (
                      p.name
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{p.org}</td>
                  <td className="px-4 py-3 text-gray-600">{p.why}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">{t('industry.capital')}</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {(industry.capital ?? []).map((c, i) => (
            <div key={i} className="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
              <p className="font-medium text-gray-900">
                {c.url ? (
                  <a href={c.url} target="_blank" rel="noopener noreferrer" className="text-blue-600">
                    {c.target}
                  </a>
                ) : (
                  c.target
                )}
              </p>
              <p className="mt-1 text-sm text-gray-600">
                {c.round} · {c.amount}
              </p>
              {c.investors && <p className="mt-1 text-xs text-gray-500">{c.investors}</p>}
            </div>
          ))}
        </div>
      </section>

      {funding.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">{t('industry.funding')}</h2>
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
        </section>
      )}

      {signals.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">{t('industry.signals_live')}</h2>
          <ul className="space-y-2">
            {signals.slice(0, 10).map((s) => (
              <li key={s.id} className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm">
                {s.url ? (
                  <a href={s.url} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600">
                    {s.title}
                  </a>
                ) : (
                  s.title
                )}
                {s.published_at && (
                  <span className="ml-2 text-xs text-gray-400">{s.published_at.slice(0, 10)}</span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
