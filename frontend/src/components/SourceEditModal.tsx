'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Source, SourceCreate, SourceUpdate, Entity, Organization, SourceExperience, SourceExperienceCreate } from '@/lib/types';
import { Modal } from '@/components/ui/Modal';
import { useLang } from '@/lib/i18n';
import { X, Plus, Trash2 } from 'lucide-react';

// Only person / organization are editable via this modal
const PERSON_ORG_TYPES = ['person', 'organization'];
const ACTIVITY = ['very_active', 'active', 'normal', 'inactive', 'unknown'];
const AFFILIATIONS = ['industry', 'academia', 'media', 'independent', 'other'];
const TIERS = ['P0+', 'P0', 'P1', 'P2', 'P3'];

const inputCls = 'w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';
const labelCls = 'block text-xs font-medium text-gray-600 mb-1';

interface Props {
  open: boolean;
  source: Source | null;
  onClose: () => void;
  onSaved: (s: Source) => void;
}

export function SourceEditModal({ open, source, onClose, onSaved }: Props) {
  const { t } = useLang();
  const [form, setForm] = useState<Partial<SourceCreate>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Research fields (topic entities) and organizations
  const [researchFields, setResearchFields] = useState<Entity[]>([]);
  const [allOrgs, setAllOrgs] = useState<Organization[]>([]);
  const [selectedFieldIds, setSelectedFieldIds] = useState<string[]>([]);

  // Experiences state (person sources only)
  const [experiences, setExperiences] = useState<SourceExperience[]>([]);
  const [newExp, setNewExp] = useState<Partial<SourceExperienceCreate>>({});
  const [addingExp, setAddingExp] = useState(false);

  // Load research fields (managed in the Research Fields page) and organizations
  useEffect(() => {
    if (!open) return;
    api.get<Entity[]>('/entities?entity_type=topic&limit=1000').then(setResearchFields).catch(() => {});
    api.get<Organization[]>('/organizations?limit=500').then(setAllOrgs).catch(() => {});
  }, [open]);

  // Load existing experiences when editing a person source
  useEffect(() => {
    if (!open || !source || source.source_type !== 'person') { setExperiences([]); return; }
    // Use experiences embedded in source (populated by API)
    setExperiences(source.experiences ?? []);
  }, [open, source]);

  // Initialise form when modal opens for a (different) source
  const [initId, setInitId] = useState<string | null>(null);
  const currentId = source?.id ?? '__new__';
  if (open && initId !== currentId) {
    setInitId(currentId);
    setForm(
      source
        ? { ...source }
        : { name: '', source_type: 'person', activity_status: 'unknown', is_active: true },
    );
    setError(null);
  }

  // Pre-select research fields by matching existing source tags by name
  useEffect(() => {
    if (!open) return;
    if (!source) { setSelectedFieldIds([]); return; }
    const tagNames = new Set(source.source_tags.map((st) => st.tag?.name).filter(Boolean));
    setSelectedFieldIds(researchFields.filter((rf) => tagNames.has(rf.name)).map((rf) => rf.id));
  }, [open, source, researchFields]);

  function set<K extends keyof SourceCreate>(key: K, value: SourceCreate[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function toggleField(id: string) {
    setSelectedFieldIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      // Strip read-only / nested fields that came from the spread Source object,
      // and send `organization_id` as null (not undefined) so clearing the org
      // actually persists — JSON.stringify drops undefined keys.
      const {
        organization: _org, source_tags: _st, experiences: _ex, accounts: _ac,
        id: _id, created_at: _c, updated_at: _u, ...rest
      } = form as Record<string, unknown>;
      const payload: SourceUpdate = {
        ...(rest as SourceUpdate),
        organization_id: form.organization_id ?? null,
        research_field_ids: selectedFieldIds,
      };
      let saved: Source;
      if (source) {
        saved = await api.patch<Source>(`/sources/${source.id}`, payload);
      } else {
        saved = await api.post<Source>('/sources', payload);
      }
      onSaved(saved);
      onClose();
    } catch (err) {
      setError(`${t('action.save_failed')}: ${String(err)}`);
    } finally {
      setSaving(false);
    }
  }

  const title = source ? t('action.edit_source') : t('sources.title');

  return (
    <Modal open={open} onClose={onClose} title={title} widthClass="max-w-3xl">
      <form onSubmit={handleSave} className="grid grid-cols-2 gap-4">

        {/* Name */}
        <div className="col-span-2">
          <label className={labelCls}>{t('sources.col.name')} *</label>
          <input required value={form.name ?? ''} onChange={(e) => set('name', e.target.value)} className={inputCls} />
        </div>

        {/* Type — only person / organization */}
        <div>
          <label className={labelCls}>{t('sources.col.type')}</label>
          <select value={form.source_type ?? 'person'} onChange={(e) => set('source_type', e.target.value)} className={inputCls}>
            {PERSON_ORG_TYPES.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        {/* Tier */}
        <div>
          <label className={labelCls}>{t('sources.col.tier')}</label>
          <select value={form.tier ?? ''} onChange={(e) => set('tier', e.target.value || undefined)} className={inputCls}>
            <option value="">—</option>
            {TIERS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        {/* Organization */}
        <div className="col-span-2">
          <label className={labelCls}>所属组织</label>
          <select
            value={form.organization_id ?? ''}
            onChange={(e) => set('organization_id', e.target.value || undefined)}
            className={inputCls}
          >
            <option value="">—</option>
            {allOrgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        </div>

        {/* Affiliation type */}
        <div>
          <label className={labelCls}>affiliation_type</label>
          <select value={form.affiliation_type ?? ''} onChange={(e) => set('affiliation_type', e.target.value || undefined)} className={inputCls}>
            <option value="">—</option>
            {AFFILIATIONS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        {/* Activity */}
        <div>
          <label className={labelCls}>{t('sources.col.activity')}</label>
          <select value={form.activity_status ?? 'unknown'} onChange={(e) => set('activity_status', e.target.value)} className={inputCls}>
            {ACTIVITY.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        {/* Role title */}
        <div className="col-span-2">
          <label className={labelCls}>role_title</label>
          <input value={form.role_title ?? ''} onChange={(e) => set('role_title', e.target.value || undefined)} className={inputCls} />
        </div>

        {/* Description */}
        <div className="col-span-2">
          <label className={labelCls}>简介</label>
          <textarea rows={2} value={form.description ?? ''} onChange={(e) => set('description', e.target.value || undefined)} className={inputCls} />
        </div>

        {/* Research fields multi-select (sourced from the Research Fields page) */}
        <div className="col-span-2">
          <label className={labelCls}>研究领域（来自研究领域库）</label>
          {selectedFieldIds.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1">
              {selectedFieldIds.map((fid) => {
                const rf = researchFields.find((r) => r.id === fid);
                return rf ? (
                  <span key={fid} className="flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                    {rf.name}
                    <button type="button" onClick={() => toggleField(fid)} className="text-blue-400 hover:text-blue-700">
                      <X size={11} />
                    </button>
                  </span>
                ) : null;
              })}
            </div>
          )}
          <div className="max-h-36 overflow-y-auto rounded-md border border-gray-200 p-2">
            {researchFields.length === 0 ? (
              <p className="text-xs text-gray-400">暂无研究领域，请先在「研究领域」页面创建</p>
            ) : (
              researchFields.map((rf) => (
                <label key={rf.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-gray-50">
                  <input
                    type="checkbox"
                    checked={selectedFieldIds.includes(rf.id)}
                    onChange={() => toggleField(rf.id)}
                    className="h-3.5 w-3.5 accent-blue-600"
                  />
                  <span className="text-sm text-gray-700">{rf.name}</span>
                  <span className="ml-auto text-[10px] uppercase text-gray-400">{rf.entity_type}</span>
                </label>
              ))
            )}
          </div>
        </div>

        {/* Scores */}
        <div>
          <label className={labelCls}>importance_score</label>
          <input type="number" step="0.05" min="0" max="1" value={form.importance_score ?? 0.5}
            onChange={(e) => set('importance_score', parseFloat(e.target.value))} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>reliability_score</label>
          <input type="number" step="0.05" min="0" max="1" value={form.reliability_score ?? 0.5}
            onChange={(e) => set('reliability_score', parseFloat(e.target.value))} className={inputCls} />
        </div>

        {/* Links */}
        <div className="col-span-2 grid grid-cols-2 gap-4 border-t border-gray-100 pt-4">
          {([
            ['twitter_url', 'Twitter'],
            ['github_url', 'GitHub'],
            ['scholar_url', 'Scholar'],
            ['openalex_url', 'OpenAlex'],
            ['personal_url', 'Homepage'],
            ['arxiv_homepage_url', 'arXiv'],
            ['arxiv_author_query', 'arXiv Query'],
            ['orcid', 'ORCID'],
          ] as const).map(([key, label]) => (
            <div key={key}>
              <label className={labelCls}>{label}</label>
              <input value={(form[key] as string) ?? ''} onChange={(e) => set(key, (e.target.value || undefined) as never)} className={inputCls} />
            </div>
          ))}
        </div>

        {/* Notes / tier_reason */}
        <div className="col-span-2">
          <label className={labelCls}>tier_reason</label>
          <textarea rows={1} value={form.tier_reason ?? ''} onChange={(e) => set('tier_reason', e.target.value || undefined)} className={inputCls} />
        </div>
        <div className="col-span-2">
          <label className={labelCls}>notes</label>
          <textarea rows={1} value={form.notes ?? ''} onChange={(e) => set('notes', e.target.value || undefined)} className={inputCls} />
        </div>

        {/* Experiences (person sources) */}
        {(form.source_type === 'person' || (!form.source_type && source?.source_type === 'person')) && source && (
          <div className="col-span-2 border-t border-gray-100 pt-4">
            <div className="mb-2 flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">经历（所属组织历史）</label>
              <button type="button" onClick={() => setAddingExp(true)}
                className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-blue-600 hover:bg-blue-50">
                <Plus size={12} /> 添加
              </button>
            </div>

            {/* Existing experiences */}
            <div className="space-y-2">
              {experiences.map((exp) => (
                <div key={exp.id} className="flex items-start gap-2 rounded-lg border border-gray-100 bg-gray-50 p-2 text-xs">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800">{exp.organization?.name ?? exp.org_name_raw ?? '—'}</p>
                    {exp.role_title && <p className="text-gray-500">{exp.role_title}</p>}
                    <p className="text-gray-400">
                      {exp.start_date ?? '?'} — {exp.is_current ? '至今' : (exp.end_date ?? '?')}
                    </p>
                  </div>
                  <button type="button"
                    onClick={async () => {
                      await api.delete(`/sources/${source.id}/experiences/${exp.id}`).catch(() => {});
                      setExperiences((prev) => prev.filter((e) => e.id !== exp.id));
                    }}
                    className="shrink-0 text-gray-300 hover:text-red-500">
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>

            {/* Add new experience form */}
            {addingExp && (
              <div className="mt-2 grid grid-cols-2 gap-2 rounded-lg border border-blue-100 bg-blue-50 p-3">
                <div className="col-span-2">
                  <label className={labelCls}>组织</label>
                  <select
                    value={newExp.organization_id ?? ''}
                    onChange={(e) => setNewExp((n) => ({ ...n, organization_id: e.target.value || undefined }))}
                    className={inputCls}
                  >
                    <option value="">— 选择或在下方填写 —</option>
                    {allOrgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
                  </select>
                </div>
                {!newExp.organization_id && (
                  <div className="col-span-2">
                    <label className={labelCls}>组织名称（手动填写）</label>
                    <input value={newExp.org_name_raw ?? ''} onChange={(e) => setNewExp((n) => ({ ...n, org_name_raw: e.target.value || undefined }))} className={inputCls} />
                  </div>
                )}
                <div>
                  <label className={labelCls}>职位</label>
                  <input value={newExp.role_title ?? ''} onChange={(e) => setNewExp((n) => ({ ...n, role_title: e.target.value || undefined }))} className={inputCls} />
                </div>
                <div className="flex items-end gap-2">
                  <label className="flex items-center gap-1 text-xs text-gray-600">
                    <input type="checkbox" checked={newExp.is_current ?? false}
                      onChange={(e) => setNewExp((n) => ({ ...n, is_current: e.target.checked }))} />
                    当前职位
                  </label>
                </div>
                <div>
                  <label className={labelCls}>开始时间 (YYYY-MM)</label>
                  <input value={newExp.start_date ?? ''} onChange={(e) => setNewExp((n) => ({ ...n, start_date: e.target.value || undefined }))} className={inputCls} placeholder="2022-03" />
                </div>
                <div>
                  <label className={labelCls}>结束时间 (YYYY-MM)</label>
                  <input value={newExp.end_date ?? ''} disabled={!!newExp.is_current} onChange={(e) => setNewExp((n) => ({ ...n, end_date: e.target.value || undefined }))} className={inputCls} placeholder="2024-06" />
                </div>
                <div className="col-span-2 flex gap-2">
                  <button type="button"
                    onClick={async () => {
                      try {
                        const saved = await api.post<SourceExperience>(
                          `/sources/${source.id}/experiences`,
                          { ...newExp, is_current: newExp.is_current ?? false },
                        );
                        setExperiences((prev) => [...prev, saved]);
                        setNewExp({});
                        setAddingExp(false);
                      } catch (err) { alert(String(err)); }
                    }}
                    className="rounded-md bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700">
                    保存
                  </button>
                  <button type="button" onClick={() => { setAddingExp(false); setNewExp({}); }}
                    className="rounded-md bg-gray-100 px-3 py-1 text-xs text-gray-600 hover:bg-gray-200">
                    取消
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Active */}
        <label className="col-span-2 flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={form.is_active ?? true} onChange={(e) => set('is_active', e.target.checked)} />
          is_active
        </label>

        {error && <p className="col-span-2 text-sm text-red-600">{error}</p>}

        <div className="col-span-2 flex gap-3 border-t border-gray-100 pt-4">
          <button type="submit" disabled={saving}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            {saving ? t('action.saving') : t('action.save')}
          </button>
          <button type="button" onClick={onClose}
            className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200">
            {t('action.cancel')}
          </button>
        </div>
      </form>
    </Modal>
  );
}
