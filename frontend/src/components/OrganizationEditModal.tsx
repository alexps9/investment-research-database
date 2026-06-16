'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Organization, TagNode } from '@/lib/types';
import { Modal } from '@/components/ui/Modal';
import { X } from 'lucide-react';

interface Props {
  open: boolean;
  org: Organization | null;
  onClose: () => void;
  onSaved: (org: Organization) => void;
}

const ORG_TYPES = ['company', 'university', 'lab', 'media', 'community', 'nonprofit', 'government', 'other'];

const labelCls = 'block text-xs font-medium text-gray-500 mb-1';
const inputCls =
  'w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';

export function OrganizationEditModal({ open, org, onClose, onSaved }: Props) {
  const [form, setForm] = useState<Partial<Organization>>({});
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [allTopics, setAllTopics] = useState<TagNode[]>([]);
  const [allOrgs, setAllOrgs] = useState<Organization[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    api.get<TagNode[]>('/tags?tag_type=topic').then(setAllTopics).catch(() => {});
    api.get<Organization[]>('/organizations?limit=500').then(setAllOrgs).catch(() => {});
  }, [open]);

  useEffect(() => {
    if (!open) { setForm({}); setSelectedTagIds([]); return; }
    if (org) {
      setForm({ ...org });
      setSelectedTagIds(org.org_tags?.map((t) => t.tag_id) ?? []);
    } else {
      setForm({ org_type: 'other', aliases: [] });
      setSelectedTagIds([]);
    }
  }, [open, org]);

  function set<K extends keyof Organization>(k: K, v: Organization[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  function toggleTopic(tagId: string) {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId],
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name?.trim()) return;
    setSaving(true);
    try {
      const payload = { ...form, tag_ids: selectedTagIds };
      let saved: Organization;
      if (org) {
        saved = await api.patch<Organization>(`/organizations/${org.id}`, payload);
      } else {
        saved = await api.post<Organization>('/organizations', payload);
      }
      onSaved(saved);
      onClose();
    } catch (err) {
      alert(String(err));
    } finally {
      setSaving(false);
    }
  }

  // exclude self from parent candidates
  const parentCandidates = allOrgs.filter((o) => !org || o.id !== org.id);

  return (
    <Modal open={open} onClose={onClose} title={org ? `编辑组织 — ${org.name}` : '新建组织'} size="md">
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
        {/* Name */}
        <div className="col-span-2">
          <label className={labelCls}>名称 *</label>
          <input required value={form.name ?? ''} onChange={(e) => set('name', e.target.value)} className={inputCls} />
        </div>

        {/* Org type */}
        <div>
          <label className={labelCls}>类型</label>
          <select value={form.org_type ?? 'other'} onChange={(e) => set('org_type', e.target.value)} className={inputCls}>
            {ORG_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        {/* Country */}
        <div>
          <label className={labelCls}>国家/地区</label>
          <input value={form.country ?? ''} onChange={(e) => set('country', e.target.value || undefined)} className={inputCls} />
        </div>

        {/* Website */}
        <div className="col-span-2">
          <label className={labelCls}>官网 URL</label>
          <input type="url" value={form.website_url ?? ''} onChange={(e) => set('website_url', e.target.value || undefined)} className={inputCls} />
        </div>

        {/* Parent org */}
        <div className="col-span-2">
          <label className={labelCls}>上属机构</label>
          <select
            value={form.parent_org_id ?? ''}
            onChange={(e) => set('parent_org_id', e.target.value || undefined)}
            className={inputCls}
          >
            <option value="">— 无 —</option>
            {parentCandidates.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        </div>

        {/* Topic fields (multi-select) */}
        <div className="col-span-2">
          <label className={labelCls}>研究/业务领域</label>
          {allTopics.length === 0 ? (
            <p className="text-xs text-gray-400">加载中…</p>
          ) : (
            <div className="max-h-40 overflow-y-auto rounded-lg border border-gray-200 bg-white p-2">
              <div className="flex flex-wrap gap-1.5">
                {allTopics.map((t) => {
                  const selected = selectedTagIds.includes(t.id);
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => toggleTopic(t.id)}
                      className={`rounded-full border px-2.5 py-0.5 text-xs transition ${
                        selected
                          ? 'border-blue-500 bg-blue-500 text-white'
                          : 'border-gray-200 text-gray-600 hover:border-blue-300'
                      }`}
                    >
                      {t.name}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Description */}
        <div className="col-span-2">
          <label className={labelCls}>简介</label>
          <textarea rows={2} value={form.description ?? ''} onChange={(e) => set('description', e.target.value || undefined)} className={inputCls} />
        </div>

        {/* Footer */}
        <div className="col-span-2 flex justify-end gap-2 border-t border-gray-100 pt-4">
          <button type="button" onClick={onClose}
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">
            取消
          </button>
          <button type="submit" disabled={saving}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            {saving ? '保存中…' : '保存'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
