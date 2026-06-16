'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { Organization, Entity, EntityRelation } from '@/lib/types';
import { Modal } from '@/components/ui/Modal';
import { Plus, Trash2, Link2 } from 'lucide-react';

interface Props {
  open: boolean;
  org: Organization | null;
  onClose: () => void;
  onSaved: (org: Organization) => void;
}

const ORG_TYPES = ['company', 'university', 'lab', 'media', 'community', 'nonprofit', 'government', 'other'];

// Organization ↔ Organization relation types (subject = this org)
const ORG_REL_TYPES: { value: string; label: string }[] = [
  { value: 'SUBSIDIARY_OF', label: '附属/子公司于' },
  { value: 'COMPETITOR_OF', label: '竞争对手' },
  { value: 'PARTNER_OF', label: '合作伙伴' },
  { value: 'ACQUIRED_BY', label: '被…收购' },
  { value: 'SPUN_OFF_FROM', label: '分拆自' },
];
const ORG_REL_SET = new Set(ORG_REL_TYPES.map((r) => r.value));
const relLabel = (v: string) => ORG_REL_TYPES.find((r) => r.value === v)?.label ?? v;

const labelCls = 'block text-xs font-medium text-gray-500 mb-1';
const inputCls =
  'w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';

export function OrganizationEditModal({ open, org, onClose, onSaved }: Props) {
  const [form, setForm] = useState<Partial<Organization>>({});
  const [selectedFieldIds, setSelectedFieldIds] = useState<string[]>([]);
  const [researchFields, setResearchFields] = useState<Entity[]>([]);
  const [allOrgs, setAllOrgs] = useState<Organization[]>([]);
  const [saving, setSaving] = useState(false);

  // Org-org relationship editing (operates on the entity graph)
  const [orgEntityId, setOrgEntityId] = useState<string | null>(null);
  const [relations, setRelations] = useState<EntityRelation[]>([]);
  const [newRelType, setNewRelType] = useState<string>('PARTNER_OF');
  const [newRelTarget, setNewRelTarget] = useState<string>('');
  const [relBusy, setRelBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    Promise.all([
      api.get<Entity[]>('/entities?entity_type=topic&limit=1000').catch(() => []),
      api.get<Entity[]>('/entities?entity_type=approach&limit=1000').catch(() => []),
    ]).then(([topics, approaches]) => setResearchFields([...topics, ...approaches]));
    api.get<Organization[]>('/organizations?limit=500').then(setAllOrgs).catch(() => {});
  }, [open]);

  useEffect(() => {
    if (!open) { setForm({}); setSelectedFieldIds([]); setRelations([]); setOrgEntityId(null); return; }
    if (org) {
      setForm({ ...org });
      const tagNames = new Set(org.org_tags?.map((t) => t.tag?.name).filter(Boolean));
      setSelectedFieldIds(researchFields.filter((rf) => tagNames.has(rf.name)).map((rf) => rf.id));
    } else {
      setForm({ org_type: 'other', aliases: [] });
      setSelectedFieldIds([]);
    }
  }, [open, org, researchFields]);

  // Bridge this organization into the entity graph and load its org-org relations
  useEffect(() => {
    if (!open || !org) return;
    let cancelled = false;
    (async () => {
      try {
        const ent = await api.post<Entity>('/entities/ensure', {
          name: org.name, canonical_name: org.name, entity_type: 'organization', metadata: {},
        });
        if (cancelled) return;
        setOrgEntityId(ent.id);
        const rels = await api.get<EntityRelation[]>(`/entities/${ent.id}/relations`);
        if (cancelled) return;
        setRelations(rels.filter((r) => ORG_REL_SET.has(r.relation_type) && r.subject_entity_id === ent.id));
      } catch { /* ignore — relations editing simply unavailable */ }
    })();
    return () => { cancelled = true; };
  }, [open, org]);

  function set<K extends keyof Organization>(k: K, v: Organization[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  function toggleField(id: string) {
    setSelectedFieldIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function addRelation() {
    if (!orgEntityId || !newRelTarget) return;
    const targetOrg = allOrgs.find((o) => o.id === newRelTarget);
    if (!targetOrg) return;
    setRelBusy(true);
    try {
      // Ensure the target organization exists as an entity
      const targetEnt = await api.post<Entity>('/entities/ensure', {
        name: targetOrg.name, canonical_name: targetOrg.name, entity_type: 'organization', metadata: {},
      });
      const rel = await api.post<EntityRelation>(`/entities/${orgEntityId}/relations`, {
        subject_entity_id: orgEntityId,
        relation_type: newRelType,
        object_entity_id: targetEnt.id,
        confidence: 1.0,
        extracted_by: 'manual',
      });
      // attach object_entity for display
      setRelations((prev) => [...prev, { ...rel, object_entity: targetEnt }]);
      setNewRelTarget('');
    } catch (err) {
      alert(String(err));
    } finally {
      setRelBusy(false);
    }
  }

  async function deleteRelation(relId: string) {
    await api.delete(`/entities/relations/${relId}`).catch(() => {});
    setRelations((prev) => prev.filter((r) => r.id !== relId));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name?.trim()) return;
    setSaving(true);
    try {
      // Strip read-only / nested fields and send parent_org_id as null (not
      // undefined) so clearing the parent org actually persists.
      const {
        org_tags: _ot, parent_org: _po, created_at: _c, updated_at: _u, id: _id, ...rest
      } = form as Record<string, unknown>;
      const payload = {
        ...rest,
        parent_org_id: form.parent_org_id ?? null,
        research_field_ids: selectedFieldIds,
      };
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

  const parentCandidates = allOrgs.filter((o) => !org || o.id !== org.id);

  return (
    <Modal open={open} onClose={onClose} title={org ? `编辑机构 — ${org.name}` : '新建机构'} widthClass="max-w-2xl">
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

        {/* Parent org (= SUBSIDIARY_OF shortcut) */}
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

        {/* Research / business fields (multi-select from Research Fields library) */}
        <div className="col-span-2">
          <label className={labelCls}>研究/业务领域（来自研究领域库）</label>
          {researchFields.length === 0 ? (
            <p className="text-xs text-gray-400">暂无研究领域，请先在「研究领域」页面创建</p>
          ) : (
            <div className="max-h-40 overflow-y-auto rounded-lg border border-gray-200 bg-white p-2">
              <div className="flex flex-wrap gap-1.5">
                {researchFields.map((rf) => {
                  const selected = selectedFieldIds.includes(rf.id);
                  return (
                    <button
                      key={rf.id}
                      type="button"
                      onClick={() => toggleField(rf.id)}
                      className={`rounded-full border px-2.5 py-0.5 text-xs transition ${
                        selected
                          ? 'border-blue-500 bg-blue-500 text-white'
                          : 'border-gray-200 text-gray-600 hover:border-blue-300'
                      }`}
                    >
                      {rf.name}
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

        {/* Organization ↔ Organization relationships */}
        {org && (
          <div className="col-span-2 border-t border-gray-100 pt-4">
            <label className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500">
              <Link2 size={13} /> 机构间关系
            </label>

            <div className="space-y-1.5">
              {relations.map((r) => (
                <div key={r.id} className="flex items-center gap-2 rounded-lg border border-gray-100 bg-gray-50 p-2 text-xs">
                  <span className="rounded bg-purple-100 px-1.5 py-0.5 font-medium text-purple-700">{relLabel(r.relation_type)}</span>
                  <span className="flex-1 truncate text-gray-700">{r.object_entity?.name ?? r.object_entity_id.slice(0, 8)}</span>
                  <button type="button" onClick={() => deleteRelation(r.id)} className="text-gray-300 hover:text-red-500">
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              {relations.length === 0 && <p className="text-xs text-gray-400">暂无关系</p>}
            </div>

            {/* Add relation */}
            <div className="mt-2 flex items-center gap-2">
              <select value={newRelType} onChange={(e) => setNewRelType(e.target.value)} className={`${inputCls} w-36`}>
                {ORG_REL_TYPES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
              <select value={newRelTarget} onChange={(e) => setNewRelTarget(e.target.value)} className={`${inputCls} flex-1`}>
                <option value="">— 选择目标机构 —</option>
                {allOrgs.filter((o) => o.id !== org.id).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
              </select>
              <button type="button" onClick={addRelation} disabled={!newRelTarget || relBusy}
                className="flex shrink-0 items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-xs text-white hover:bg-blue-700 disabled:opacity-50">
                <Plus size={13} /> 添加
              </button>
            </div>
          </div>
        )}

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
