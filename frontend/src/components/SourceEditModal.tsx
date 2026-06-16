'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Source, SourceCreate, SourceUpdate, TagNode, Organization } from '@/lib/types';
import { Modal } from '@/components/ui/Modal';
import { useLang } from '@/lib/i18n';
import { X, ChevronDown } from 'lucide-react';

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

  // Available topics and organizations
  const [allTopics, setAllTopics] = useState<TagNode[]>([]);
  const [allOrgs, setAllOrgs] = useState<Organization[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);

  // Load topics and organizations once
  useEffect(() => {
    if (!open) return;
    api.get<TagNode[]>('/tags?tag_type=topic').then(setAllTopics).catch(() => {});
    api.get<Organization[]>('/organizations?limit=500').then(setAllOrgs).catch(() => {});
  }, [open]);

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
    setSelectedTagIds(source ? source.source_tags.map((st) => st.tag_id) : []);
    setError(null);
  }

  function set<K extends keyof SourceCreate>(key: K, value: SourceCreate[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function toggleTag(id: string) {
    setSelectedTagIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload: SourceUpdate = { ...form, tag_ids: selectedTagIds };
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

        {/* Topics multi-select */}
        <div className="col-span-2">
          <label className={labelCls}>研究领域（Topics）</label>
          {selectedTagIds.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1">
              {selectedTagIds.map((tid) => {
                const tag = allTopics.find((t) => t.id === tid);
                return tag ? (
                  <span key={tid} className="flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                    {tag.name}
                    <button type="button" onClick={() => toggleTag(tid)} className="text-blue-400 hover:text-blue-700">
                      <X size={11} />
                    </button>
                  </span>
                ) : null;
              })}
            </div>
          )}
          <div className="max-h-36 overflow-y-auto rounded-md border border-gray-200 p-2">
            {allTopics.length === 0 ? (
              <p className="text-xs text-gray-400">暂无 topic，请先在研究领域页面创建</p>
            ) : (
              allTopics.map((tag) => (
                <label key={tag.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-gray-50">
                  <input
                    type="checkbox"
                    checked={selectedTagIds.includes(tag.id)}
                    onChange={() => toggleTag(tag.id)}
                    className="h-3.5 w-3.5 accent-blue-600"
                  />
                  <span className="text-sm text-gray-700">{tag.name}</span>
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
