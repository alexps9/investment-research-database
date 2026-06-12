'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import type { Source, SourceCreate, SourceUpdate } from '@/lib/types';
import { Modal } from '@/components/ui/Modal';
import { useLang } from '@/lib/i18n';

const SOURCE_TYPES = ['person', 'organization', 'rss', 'website', 'github_repo', 'arxiv_category', 'newsletter', 'social_account'];
const ACTIVITY = ['very_active', 'active', 'normal', 'inactive', 'unknown'];
const AFFILIATIONS = ['industry', 'academia', 'media', 'independent', 'other'];
const TIERS = ['P0+', 'P0', 'P1', 'P2', 'P3'];
const SECTORS = ['industry', 'academia', 'media', 'other'];

const inputCls = 'w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';
const labelCls = 'block text-xs font-medium text-gray-600 mb-1';

interface Props {
  open: boolean;
  source: Source | null;   // null = create mode
  onClose: () => void;
  onSaved: (s: Source) => void;
}

export function SourceEditModal({ open, source, onClose, onSaved }: Props) {
  const { t } = useLang();
  const [form, setForm] = useState<Partial<SourceCreate>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // initialise form whenever the modal opens for a (different) source
  const [initId, setInitId] = useState<string | null>(null);
  const currentId = source?.id ?? '__new__';
  if (open && initId !== currentId) {
    setInitId(currentId);
    setForm(source ? { ...source } : { name: '', source_type: 'person', activity_status: 'unknown', is_active: true });
    setError(null);
  }

  function set<K extends keyof SourceCreate>(key: K, value: SourceCreate[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      let saved: Source;
      if (source) {
        const payload: SourceUpdate = { ...form };
        saved = await api.patch<Source>(`/sources/${source.id}`, payload);
      } else {
        saved = await api.post<Source>('/sources', form);
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
        <div className="col-span-2">
          <label className={labelCls}>{t('sources.col.name')} *</label>
          <input required value={form.name ?? ''} onChange={(e) => set('name', e.target.value)} className={inputCls} />
        </div>

        <div>
          <label className={labelCls}>{t('sources.col.type')}</label>
          <select value={form.source_type ?? 'person'} onChange={(e) => set('source_type', e.target.value)} className={inputCls}>
            {SOURCE_TYPES.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div>
          <label className={labelCls}>{t('sources.col.tier')}</label>
          <select value={form.tier ?? ''} onChange={(e) => set('tier', e.target.value || undefined)} className={inputCls}>
            <option value="">—</option>
            {TIERS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        <div>
          <label className={labelCls}>{t('sources.col.sector')}</label>
          <select value={form.sector ?? ''} onChange={(e) => set('sector', e.target.value || undefined)} className={inputCls}>
            <option value="">—</option>
            {SECTORS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div>
          <label className={labelCls}>{t('sources.col.activity')}</label>
          <select value={form.activity_status ?? 'unknown'} onChange={(e) => set('activity_status', e.target.value)} className={inputCls}>
            {ACTIVITY.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        <div>
          <label className={labelCls}>affiliation_type</label>
          <select value={form.affiliation_type ?? ''} onChange={(e) => set('affiliation_type', e.target.value || undefined)} className={inputCls}>
            <option value="">—</option>
            {AFFILIATIONS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div>
          <label className={labelCls}>source_authority</label>
          <input value={form.source_authority ?? ''} onChange={(e) => set('source_authority', e.target.value || undefined)} className={inputCls} />
        </div>

        <div className="col-span-2">
          <label className={labelCls}>research_focus</label>
          <input value={form.research_focus ?? ''} onChange={(e) => set('research_focus', e.target.value || undefined)} className={inputCls} />
        </div>

        <div className="col-span-2">
          <label className={labelCls}>description</label>
          <textarea rows={2} value={form.description ?? ''} onChange={(e) => set('description', e.target.value || undefined)} className={inputCls} />
        </div>
        <div className="col-span-2">
          <label className={labelCls}>tier_reason</label>
          <textarea rows={2} value={form.tier_reason ?? ''} onChange={(e) => set('tier_reason', e.target.value || undefined)} className={inputCls} />
        </div>
        <div className="col-span-2">
          <label className={labelCls}>notes</label>
          <textarea rows={2} value={form.notes ?? ''} onChange={(e) => set('notes', e.target.value || undefined)} className={inputCls} />
        </div>

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

        <div className="col-span-2 grid grid-cols-2 gap-4 border-t border-gray-100 pt-4">
          {([
            ['twitter_url', 'Twitter'],
            ['github_url', 'GitHub'],
            ['scholar_url', 'Scholar'],
            ['openalex_url', 'OpenAlex'],
            ['personal_url', 'Homepage'],
            ['arxiv_homepage_url', 'arXiv'],
            ['arxiv_author_query', 'arxiv_author_query'],
            ['orcid', 'ORCID'],
          ] as const).map(([key, label]) => (
            <div key={key}>
              <label className={labelCls}>{label}</label>
              <input value={(form[key] as string) ?? ''} onChange={(e) => set(key, (e.target.value || undefined) as never)} className={inputCls} />
            </div>
          ))}
        </div>

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
