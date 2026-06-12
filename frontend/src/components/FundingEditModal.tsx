'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import type { FundingEvent, FundingCreate } from '@/lib/types';
import { Modal } from '@/components/ui/Modal';
import { useLang } from '@/lib/i18n';

const inputCls = 'w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';
const labelCls = 'block text-xs font-medium text-gray-600 mb-1';

interface Props {
  open: boolean;
  funding: FundingEvent | null;   // null = create mode
  onClose: () => void;
  onSaved: (f: FundingEvent) => void;
}

export function FundingEditModal({ open, funding, onClose, onSaved }: Props) {
  const { t } = useLang();
  const [form, setForm] = useState<Partial<FundingEvent>>({});
  const [investorsText, setInvestorsText] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [initId, setInitId] = useState<string | null>(null);
  const currentId = funding?.id ?? '__new__';
  if (open && initId !== currentId) {
    setInitId(currentId);
    setForm(funding ? { ...funding } : { company_name: '', extracted_by: 'manual' });
    setInvestorsText(funding?.investors?.join(', ') ?? '');
    setError(null);
  }

  function set<K extends keyof FundingEvent>(key: K, value: FundingEvent[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const investors = investorsText.split(',').map((s) => s.trim()).filter(Boolean);
    const payload: Partial<FundingCreate> = {
      company_name: form.company_name,
      round: form.round || undefined,
      amount_usd: form.amount_usd != null ? Number(form.amount_usd) : undefined,
      currency: form.currency || undefined,
      sector: form.sector || undefined,
      investors,
      announced_at: form.announced_at || undefined,
      source_url: form.source_url || undefined,
      description: form.description || undefined,
      extracted_by: form.extracted_by || 'manual',
    };
    try {
      const saved = funding
        ? await api.patch<FundingEvent>(`/funding/${funding.id}`, payload)
        : await api.post<FundingEvent>('/funding', payload);
      onSaved(saved);
      onClose();
    } catch (err) {
      setError(`${t('action.save_failed')}: ${String(err)}`);
    } finally {
      setSaving(false);
    }
  }

  const title = funding ? t('funding.edit') : t('funding.new');
  const dateValue = form.announced_at ? form.announced_at.slice(0, 10) : '';

  return (
    <Modal open={open} onClose={onClose} title={title} widthClass="max-w-2xl">
      <form onSubmit={handleSave} className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className={labelCls}>{t('funding.field.company')} *</label>
          <input required value={form.company_name ?? ''} onChange={(e) => set('company_name', e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>{t('funding.field.round')}</label>
          <input value={form.round ?? ''} onChange={(e) => set('round', e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>{t('funding.field.amount')}</label>
          <input type="number" step="any" value={form.amount_usd ?? ''} onChange={(e) => set('amount_usd', e.target.value === '' ? undefined : Number(e.target.value))} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>{t('funding.field.currency')}</label>
          <input value={form.currency ?? ''} onChange={(e) => set('currency', e.target.value)} className={inputCls} placeholder="USD" />
        </div>
        <div>
          <label className={labelCls}>{t('funding.field.sector')}</label>
          <input value={form.sector ?? ''} onChange={(e) => set('sector', e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>{t('funding.field.date')}</label>
          <input type="date" value={dateValue} onChange={(e) => set('announced_at', e.target.value ? `${e.target.value}T00:00:00Z` : undefined)} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>{t('funding.field.source')}</label>
          <input type="url" value={form.source_url ?? ''} onChange={(e) => set('source_url', e.target.value)} className={inputCls} />
        </div>
        <div className="col-span-2">
          <label className={labelCls}>{t('funding.field.investors')}</label>
          <input value={investorsText} onChange={(e) => setInvestorsText(e.target.value)} className={inputCls} placeholder="Sequoia, a16z, ..." />
        </div>
        <div className="col-span-2">
          <label className={labelCls}>{t('funding.field.desc')}</label>
          <textarea rows={3} value={form.description ?? ''} onChange={(e) => set('description', e.target.value || undefined)} className={inputCls} />
        </div>

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
