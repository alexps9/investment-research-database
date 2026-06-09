'use client';

import { useMemo } from 'react';
import { useRouter } from 'next/navigation';
import type { Entity, EntityRelation } from '@/lib/types';
import KnowledgeGraph, { type GraphNode, type GraphLink } from './KnowledgeGraph';

interface Props {
  entity: Entity;
  outgoing: EntityRelation[];
  incoming: EntityRelation[];
  related: Entity[];
}

export default function EntityEgoGraph({ entity, outgoing, incoming, related }: Props) {
  const router = useRouter();

  const { nodes, links } = useMemo(() => {
    const lookup = new Map<string, { name: string; type: string }>();
    lookup.set(entity.id, { name: entity.name, type: entity.entity_type });
    related.forEach((e) => lookup.set(e.id, { name: e.name, type: e.entity_type }));
    outgoing.forEach((r) => {
      if (r.object_entity) lookup.set(r.object_entity_id, { name: r.object_entity.name, type: r.object_entity.entity_type });
    });
    incoming.forEach((r) => {
      if (r.subject) lookup.set(r.subject_entity_id, { name: r.subject.name, type: r.subject.entity_type });
    });

    const links: GraphLink[] = [];
    outgoing.forEach((r) => {
      if (lookup.has(r.object_entity_id)) {
        links.push({ id: r.id, source: entity.id, target: r.object_entity_id, label: r.relation_type });
      }
    });
    incoming.forEach((r) => {
      if (lookup.has(r.subject_entity_id)) {
        links.push({ id: r.id, source: r.subject_entity_id, target: entity.id, label: r.relation_type });
      }
    });

    const nodes: GraphNode[] = Array.from(lookup.entries()).map(([id, v]) => ({ id, name: v.name, type: v.type }));
    return { nodes, links };
  }, [entity, outgoing, incoming, related]);

  if (links.length === 0) return null;

  return (
    <div className="h-[360px] w-full overflow-hidden rounded-xl border border-gray-200 bg-slate-50">
      <KnowledgeGraph
        nodes={nodes}
        links={links}
        compact
        onSelect={(n) => {
          if (n && n.id !== entity.id) router.push(`/wiki/entities/${n.id}`);
        }}
      />
    </div>
  );
}
