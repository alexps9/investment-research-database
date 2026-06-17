'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { WikiEntityProfile, EntityRelation } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import EntityEgoGraph from '@/components/graph/EntityEgoGraph';
import { entityColor, entityTypeLabel } from '@/lib/entityColors';
import { useLang } from '@/lib/i18n';
import Link from 'next/link';
import { ExternalLink, ArrowLeft, Network, Loader2 } from 'lucide-react';

// Friendly, direction-aware labels for relation types (subject's perspective).
const REL_LABELS: Record<string, { out: string; in: string }> = {
  AUTHORED:      { out: '作者 · Authors',          in: '论文 / 著作 · Authored works' },
  FOCUSES_ON:    { out: '聚焦领域 · Focuses on',    in: '相关条目 · Featured in' },
  SUBTOPIC_OF:   { out: '上级主题 · Parent topic',  in: '子主题 · Sub-topics' },
  HAS_SUBTOPIC:  { out: '子主题 · Sub-topics',      in: '上级主题 · Parent topic' },
  BUILT_ON:      { out: '基于 / 继承自 · Builds on', in: '被继承 · Successors' },
  WORKS_AT:      { out: '任职于 · Works at',         in: '成员 · Members' },
  PRE_WORKED_AT: { out: '曾任职 · Previously at',    in: '前成员 · Former members' },
  GRADUATED_FROM:{ out: '毕业于 · Graduated from',   in: '校友 · Alumni' },
  FOUNDED:       { out: '创立 · Founded',            in: '创始人 · Founders' },
  SUBSIDIARY_OF: { out: '隶属 · Subsidiary of',      in: '下属机构 · Subsidiaries' },
  CO_AUTHOR:     { out: '合作者 · Co-authors',       in: '合作者 · Co-authors' },
  CO_WORK:       { out: '同事 · Colleagues',         in: '同事 · Colleagues' },
  RELATED_TO:    { out: '相关 · Related',            in: '相关 · Related' },
  COMPETES_WITH: { out: '竞争 · Competes with',      in: '竞争 · Competes with' },
};

function relLabel(type: string, dir: 'out' | 'in'): string {
  return REL_LABELS[type]?.[dir] ?? `${type} ${dir === 'out' ? '→' : '←'}`;
}

interface GroupItem { id: string; name: string; type: string }

function TypePill({ type }: { type: string }) {
  const { lang } = useLang();
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
      style={{ backgroundColor: entityColor(type) }}>
      {entityTypeLabel(type, lang)}
    </span>
  );
}

// Curated, human-readable infobox rows from entity metadata + linked source.
const INFOBOX_META: { key: string; label: string; href?: (v: string) => string }[] = [
  { key: 'org', label: '机构 / Org' },
  { key: 'organization', label: '机构 / Org' },
  { key: 'role_title', label: '职位 / Role' },
  { key: 'year', label: '年份 / Year' },
  { key: 'cited_by_count', label: '被引 / Citations' },
  { key: 'arxiv_id', label: 'arXiv', href: (v) => `https://arxiv.org/abs/${v}` },
  { key: 'doi', label: 'DOI', href: (v) => `https://doi.org/${v}` },
  { key: 'tier', label: '层级 / Tier' },
  { key: 'sector', label: '领域 / Sector' },
  { key: 'level', label: '层级 / Level' },
];

export default function WikiEntityClient({ id }: { id: string }) {
  const { lang } = useLang();
  const [profile, setProfile] = useState<WikiEntityProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    api.get<WikiEntityProfile>(`/wiki/entities/${id}`)
      .then(setProfile)
      .catch((err: Error) => { if (err.message.startsWith('404')) setNotFound(true); })
      .finally(() => setLoading(false));
  }, [id]);

  // Group all relations by (relation_type, direction) into encyclopedic sections.
  const relGroups = useMemo(() => {
    if (!profile) return [] as { label: string; items: GroupItem[] }[];
    const groups = new Map<string, GroupItem[]>();
    const add = (label: string, item: GroupItem) => {
      const arr = groups.get(label) ?? [];
      if (!arr.some((x) => x.id === item.id)) arr.push(item);
      groups.set(label, arr);
    };
    for (const rel of profile.outgoing_relations as EntityRelation[]) {
      const o = rel.object_entity;
      if (o) add(relLabel(rel.relation_type, 'out'), { id: rel.object_entity_id, name: o.name, type: o.entity_type });
    }
    for (const rel of profile.incoming_relations as EntityRelation[]) {
      const s = rel.subject;
      if (s) add(relLabel(rel.relation_type, 'in'), { id: rel.subject_entity_id, name: s.name, type: s.entity_type });
    }
    return Array.from(groups.entries()).map(([label, items]) => ({ label, items }));
  }, [profile]);

  if (loading) {
    return <div className="flex h-64 items-center justify-center text-gray-400">
      <Loader2 size={24} className="animate-spin mr-2" /> Loading…
    </div>;
  }
  if (notFound || !profile) {
    return <div className="p-8">
      <Link href="/explore" className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-blue-600">
        <ArrowLeft size={14} /> 返回 / Back
      </Link>
      <p className="text-gray-500">Entity not found.</p>
    </div>;
  }

  const { entity, aliases, related_signals, outgoing_relations, incoming_relations, related_entities, source } = profile;
  const meta = (entity.metadata ?? {}) as Record<string, unknown>;

  const sourceLinks: { label: string; url?: string }[] = source ? [
    { label: 'Homepage', url: source.personal_url },
    { label: 'Twitter', url: source.twitter_url },
    { label: 'GitHub', url: source.github_url },
    { label: 'Scholar', url: source.scholar_url },
    { label: 'OpenAlex', url: source.openalex_url },
    { label: 'arXiv', url: source.arxiv_homepage_url },
    { label: 'ORCID', url: source.orcid ? (source.orcid.startsWith('http') ? source.orcid : `https://orcid.org/${source.orcid}`) : undefined },
  ].filter((l) => l.url) : [];

  // Build infobox rows from metadata (curated) + linked source organisation.
  const infoboxRows: { label: string; value: string; href?: string }[] = [];
  const seen = new Set<string>();
  for (const def of INFOBOX_META) {
    const raw = meta[def.key];
    if (raw === undefined || raw === null || raw === '' || seen.has(def.label)) continue;
    seen.add(def.label);
    const value = String(raw);
    infoboxRows.push({ label: def.label, value, href: def.href ? def.href(value) : undefined });
  }
  if (source?.organization && !seen.has('机构 / Org')) {
    infoboxRows.push({ label: '机构 / Org', value: source.organization.name });
  }
  if (source?.role_title && !seen.has('职位 / Role')) {
    infoboxRows.push({ label: '职位 / Role', value: source.role_title });
  }

  const categories = Array.from(new Set([
    entityTypeLabel(entity.entity_type, lang),
    ...(typeof meta.lane === 'string' ? [String(meta.lane)] : []),
  ]));

  return (
    <div className="p-8 max-w-5xl">
      <Link href="/explore" className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-blue-600">
        <ArrowLeft size={14} /> 返回 / Back
      </Link>

      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold text-gray-900">{entity.name}</h1>
          <TypePill type={entity.entity_type} />
        </div>
        {entity.introduction && <p className="leading-relaxed text-gray-700">{entity.introduction}</p>}
        {entity.homepage_url && (
          <a href={entity.homepage_url} target="_blank" rel="noreferrer"
            className="mt-1 flex items-center gap-1 text-sm text-blue-600 hover:underline">
            {entity.homepage_url} <ExternalLink size={12} />
          </a>
        )}
        {aliases.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-1">
            <span className="mr-1 text-xs text-gray-400">又称 / Also known as:</span>
            {aliases.map((a) => <Badge key={a.id} variant="gray">{a.alias}</Badge>)}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main column */}
        <div className="space-y-6 lg:col-span-2">
          {(outgoing_relations.length > 0 || incoming_relations.length > 0) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-1.5">
                  <Network size={14} className="text-blue-600" /> 关系图谱 / Relationship graph
                </CardTitle>
              </CardHeader>
              <CardContent>
                <EntityEgoGraph entity={entity} outgoing={outgoing_relations} incoming={incoming_relations} related={related_entities} />
                <p className="mt-2 text-xs text-gray-400">点击节点跳转，拖拽重排，滚动缩放。</p>
              </CardContent>
            </Card>
          )}

          {relGroups.length > 0 && (
            <Card>
              <CardHeader><CardTitle>关系 / Relations</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {relGroups.map((g) => (
                  <div key={g.label}>
                    <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">{g.label}</p>
                    <div className="flex flex-wrap gap-2">
                      {g.items.map((it) => (
                        <Link key={it.id} href={`/wiki/entities/${it.id}`}
                          className="flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-sm transition-colors hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700">
                          <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: entityColor(it.type) }} />
                          {it.name}
                        </Link>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {related_signals.length > 0 && (
            <Card>
              <CardHeader><CardTitle>相关动态 / References ({related_signals.length})</CardTitle></CardHeader>
              <CardContent className="p-0">
                <ul className="divide-y divide-gray-100">
                  {related_signals.map((sig) => (
                    <li key={sig.id} className="px-5 py-3">
                      <div className="flex items-start gap-2">
                        <Badge>{sig.signal_type}</Badge>
                        <a href={sig.url} target="_blank" rel="noreferrer"
                          className="flex items-start gap-1 text-sm font-medium text-gray-900 hover:text-blue-600">
                          {sig.title} <ExternalLink size={11} className="mt-0.5 shrink-0" />
                        </a>
                      </div>
                      {sig.analysis?.tldr && <p className="mt-1 pl-1 text-xs text-gray-500">{sig.analysis.tldr}</p>}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {related_entities.length > 0 && (
            <Card>
              <CardHeader><CardTitle>参见 / See also</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {related_entities.map((ent) => (
                    <Link key={ent.id} href={`/wiki/entities/${ent.id}`}
                      className="flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-sm transition-colors hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700">
                      <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: entityColor(ent.entity_type) }} />
                      {ent.name}
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Infobox sidebar */}
        <div className="space-y-6">
          {(infoboxRows.length > 0 || sourceLinks.length > 0) && (
            <Card>
              <CardHeader><CardTitle>信息框 / Infobox</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                <dl className="space-y-2">
                  <div className="flex justify-between gap-3">
                    <dt className="text-gray-500">类型 / Type</dt>
                    <dd className="text-right"><TypePill type={entity.entity_type} /></dd>
                  </div>
                  {infoboxRows.map((r) => (
                    <div key={r.label} className="flex justify-between gap-3">
                      <dt className="shrink-0 text-gray-500">{r.label}</dt>
                      <dd className="text-right font-medium text-gray-800">
                        {r.href ? (
                          <a href={r.href} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{r.value}</a>
                        ) : r.value}
                      </dd>
                    </div>
                  ))}
                </dl>
                {sourceLinks.length > 0 && (
                  <div className="flex flex-wrap gap-2 border-t border-gray-100 pt-3">
                    {sourceLinks.map((l) => (
                      <a key={l.label} href={l.url} target="_blank" rel="noreferrer"
                        className="flex items-center gap-1 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-medium text-blue-600 hover:border-blue-300 hover:bg-blue-50">
                        {l.label} <ExternalLink size={11} />
                      </a>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {source?.experiences && source.experiences.length > 0 && (
            <Card>
              <CardHeader><CardTitle>经历 / Experience</CardTitle></CardHeader>
              <CardContent>
                <ul className="space-y-1.5">
                  {source.experiences.map((exp) => (
                    <li key={exp.id} className="text-sm text-gray-700">
                      <span className="font-medium">{exp.organization?.name ?? exp.org_name_raw ?? '—'}</span>
                      {exp.role_title && <span className="text-gray-500"> · {exp.role_title}</span>}
                      <span className="ml-1 text-xs text-gray-400">
                        ({exp.start_date ?? '?'} — {exp.is_current ? '至今' : (exp.end_date ?? '?')})
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {categories.length > 0 && (
            <Card>
              <CardHeader><CardTitle>分类 / Categories</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {categories.map((c) => <Badge key={c} variant="gray">{c}</Badge>)}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
