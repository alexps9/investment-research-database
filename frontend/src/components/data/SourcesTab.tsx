'use client';
import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import type { Source, Organization } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Plus, ExternalLink, Pencil, Trash2, Search } from 'lucide-react';
import { useLang } from '@/lib/i18n';
import { SourceEditModal } from '@/components/SourceEditModal';
import { OrganizationEditModal } from '@/components/OrganizationEditModal';
import { downloadCsv, type CsvColumn } from '@/lib/csv';
import { useRowSelection, Checkbox, ExportBar } from './selection';

const activityColor: Record<string, 'green' | 'blue' | 'yellow' | 'gray'> = {
  very_active: 'green', active: 'blue', normal: 'yellow', inactive: 'gray', unknown: 'gray',
};

const CSV_COLUMNS: CsvColumn<Source>[] = [
  { key: 'id', header: 'id' },
  { key: 'name', header: 'name' },
  { key: 'source_type', header: 'source_type' },
  { key: 'tier', header: 'tier' },
  { key: 'sector', header: 'sector' },
  { key: 'organization', header: 'organization', get: (s) => s.organization?.name ?? '' },
  { key: 'activity_status', header: 'activity_status' },
  { key: 'importance_score', header: 'importance_score' },
  { key: 'reliability_score', header: 'reliability_score' },
  { key: 'description', header: 'description' },
];

interface Props {
  /** 'person' | 'organization' | undefined = show all */
  sourceType?: 'person' | 'organization';
}

export function SourcesTab({ sourceType }: Props) {
  const { t } = useLang();
  const [sources, setSources] = useState<Source[]>([]);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Source | null>(null);
  const [orgModalOpen, setOrgModalOpen] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [q, setQ] = useState('');
  const { selected, toggle, setAll, clear } = useRowSelection();

  useEffect(() => {
    setLoading(true);
    const url = sourceType ? `/sources?limit=2000&source_type=${sourceType}` : '/sources?limit=2000';
    api.get<Source[]>(url).then(setSources).catch(console.error).finally(() => setLoading(false));
    api.get<Organization[]>('/organizations?limit=500').then(setOrgs).catch(console.error);
  }, [sourceType]);

  function handleSaved(saved: Source) {
    setSources((prev) => {
      const idx = prev.findIndex((s) => s.id === saved.id);
      if (idx === -1) return [saved, ...prev];
      const next = [...prev];
      next[idx] = saved;
      return next;
    });
  }

  function handleOrgSaved(saved: Organization) {
    setOrgs((prev) => {
      const idx = prev.findIndex((o) => o.id === saved.id);
      if (idx === -1) return [saved, ...prev];
      const next = [...prev];
      next[idx] = saved;
      return next;
    });
  }

  async function handleDelete(src: Source) {
    if (!confirm(t('action.confirm_delete').replace('{name}', src.name))) return;
    try {
      await api.delete(`/sources/${src.id}`);
      setSources((prev) => prev.filter((s) => s.id !== src.id));
    } catch (err) {
      alert(`${t('action.delete_failed')}: ${String(err)}`);
    }
  }

  const filtered = useMemo(() => {
    const k = q.trim().toLowerCase();
    if (!k) return sources;
    return sources.filter((s) =>
      s.name.toLowerCase().includes(k) ||
      (s.organization?.name ?? '').toLowerCase().includes(k) ||
      (s.sector ?? '').toLowerCase().includes(k),
    );
  }, [sources, q]);

  const allChecked = filtered.length > 0 && filtered.every((s) => selected.has(s.id));

  const isOrgView = sourceType === 'organization';

  return (
    <div>
      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-72 max-w-full">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={isOrgView ? '搜索机构…' : t('data.search.sources')}
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          {!isOrgView && (
            <ExportBar
              count={selected.size}
              onExportSelected={() => downloadCsv(sources.filter((s) => selected.has(s.id)), CSV_COLUMNS, 'sources')}
              onExportAll={() => downloadCsv(filtered, CSV_COLUMNS, 'sources')}
              onClear={clear}
            />
          )}
          {isOrgView ? (
            <button
              onClick={() => { setEditingOrg(null); setOrgModalOpen(true); }}
              className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
            >
              <Plus size={16} /> 新建机构
            </button>
          ) : (
            <button
              onClick={() => { setEditing(null); setModalOpen(true); }}
              className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
            >
              <Plus size={16} /> {t('action.new')}
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">{t('common.loading')}</p>
      ) : isOrgView ? (
        /* ── Organization table ─────────────────────────────────────────────── */
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50/80 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3">名称</th>
                <th className="px-4 py-3">类型</th>
                <th className="px-4 py-3">上属机构</th>
                <th className="px-4 py-3">领域</th>
                <th className="px-4 py-3 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {orgs.map((org) => {
                const parentOrg = org.parent_org_id ? orgs.find((o) => o.id === org.parent_org_id) : null;
                return (
                  <tr key={org.id} className="transition-colors hover:bg-blue-50/40">
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {org.name}
                      {org.website_url && (
                        <a href={org.website_url} target="_blank" rel="noreferrer"
                          className="ml-2 text-blue-400 hover:text-blue-600">
                          <ExternalLink size={12} className="inline" />
                        </a>
                      )}
                    </td>
                    <td className="px-4 py-3"><Badge variant="gray">{org.org_type}</Badge></td>
                    <td className="px-4 py-3 text-xs text-gray-500">{parentOrg?.name ?? '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {org.org_tags?.slice(0, 3).map((ot) => (
                          <Badge key={ot.tag_id} variant="blue">{ot.tag?.name ?? ot.tag_id.slice(0, 6)}</Badge>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => { setEditingOrg(org); setOrgModalOpen(true); }}
                          className="rounded-md p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-600">
                          <Pencil size={15} />
                        </button>
                        <button onClick={async () => {
                          if (!confirm(`确定删除 "${org.name}"?`)) return;
                          await api.delete(`/organizations/${org.id}`).catch((e) => alert(String(e)));
                          setOrgs((prev) => prev.filter((o) => o.id !== org.id));
                        }}
                          className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600">
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {orgs.length === 0 && <p className="px-4 py-10 text-center text-sm text-gray-400">{t('common.empty')}</p>}
        </div>
      ) : (
        /* ── Person / source table ──────────────────────────────────────────── */
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50/80 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="w-10 px-4 py-3">
                  <Checkbox checked={allChecked} onChange={() => setAll(filtered.map((s) => s.id), !allChecked)} indeterminate={selected.size > 0} />
                </th>
                <th className="px-4 py-3">{t('sources.col.name')}</th>
                <th className="px-4 py-3">{t('sources.col.tier')}</th>
                {sourceType === 'person' && <th className="px-4 py-3">所属组织</th>}
                {sourceType === 'person' && <th className="px-4 py-3">研究领域</th>}
                {!sourceType && <th className="px-4 py-3">类型</th>}
                <th className="px-4 py-3">{t('sources.col.activity')}</th>
                <th className="px-4 py-3">Links</th>
                <th className="px-4 py-3 text-right">{t('action.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((src) => (
                <tr key={src.id} className={`transition-colors hover:bg-blue-50/40 ${selected.has(src.id) ? 'bg-blue-50/60' : ''}`}>
                  <td className="px-4 py-3"><Checkbox checked={selected.has(src.id)} onChange={() => toggle(src.id)} /></td>
                  <td className="px-4 py-3 font-medium text-gray-900">{src.name}</td>
                  <td className="px-4 py-3">{src.tier ? <Badge variant="purple">{src.tier}</Badge> : <span className="text-gray-300">—</span>}</td>
                  {sourceType === 'person' && (
                    <td className="px-4 py-3 text-xs text-gray-500">{src.organization?.name ?? '—'}</td>
                  )}
                  {sourceType === 'person' && (
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {src.source_tags.slice(0, 3).map((st) => (
                          <Badge key={st.tag_id} variant="blue">{st.tag?.name ?? st.tag_id.slice(0, 6)}</Badge>
                        ))}
                      </div>
                    </td>
                  )}
                  {!sourceType && (
                    <td className="px-4 py-3"><Badge variant="gray">{src.source_type}</Badge></td>
                  )}
                  <td className="px-4 py-3">
                    <Badge variant={activityColor[src.activity_status] ?? 'gray'}>{src.activity_status}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {src.accounts.map((acc) => (
                        <a key={acc.id} href={acc.url} target="_blank" rel="noreferrer"
                          className="flex items-center gap-0.5 text-xs text-blue-600 hover:underline">
                          {acc.platform} <ExternalLink size={10} />
                        </a>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => { setEditing(src); setModalOpen(true); }}
                        className="rounded-md p-1.5 text-gray-400 hover:bg-blue-50 hover:text-blue-600" title={t('action.edit')}>
                        <Pencil size={15} />
                      </button>
                      <button onClick={() => handleDelete(src)}
                        className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600" title={t('action.delete')}>
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && <p className="px-4 py-10 text-center text-sm text-gray-400">{t('common.empty')}</p>}
        </div>
      )}

      <SourceEditModal open={modalOpen} source={editing} onClose={() => setModalOpen(false)} onSaved={handleSaved} />
      <OrganizationEditModal open={orgModalOpen} org={editingOrg} onClose={() => setOrgModalOpen(false)} onSaved={handleOrgSaved} />
    </div>
  );
}
