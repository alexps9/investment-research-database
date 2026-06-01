import { api } from '@/lib/api';
import type { EntityRelation } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

async function getRelations(): Promise<EntityRelation[]> {
  try { return await api.get<EntityRelation[]>('/graph/relations'); }
  catch { return []; }
}

export default async function GraphLitePage() {
  const relations = await getRelations();

  const nodeSet = new Map<string, { id: string; name: string; type: string }>();
  for (const rel of relations) {
    if (rel.subject) nodeSet.set(rel.subject_entity_id, { id: rel.subject_entity_id, name: rel.subject.name, type: rel.subject.entity_type });
    if (rel.object_entity) nodeSet.set(rel.object_entity_id, { id: rel.object_entity_id, name: rel.object_entity.name, type: rel.object_entity.entity_type });
  }
  const nodes = Array.from(nodeSet.values());

  return (
    <div className="p-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900">Graph Lite</h1>
      <p className="mb-6 text-sm text-gray-500">
        Entity relation graph from PostgreSQL. {nodes.length} nodes, {relations.length} edges.
      </p>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Nodes ({nodes.length})</CardTitle></CardHeader>
          <CardContent className="p-0">
            {nodes.length === 0 ? (
              <p className="px-5 py-4 text-sm text-gray-400">No nodes.</p>
            ) : (
              <ul className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
                {nodes.map(n => (
                  <li key={n.id} className="flex items-center justify-between px-5 py-2.5">
                    <Link href={`/wiki/entities/${n.id}`} className="text-sm font-medium text-gray-800 hover:text-blue-600">
                      {n.name}
                    </Link>
                    <Badge>{n.type}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Edges ({relations.length})</CardTitle></CardHeader>
          <CardContent className="p-0">
            {relations.length === 0 ? (
              <p className="px-5 py-4 text-sm text-gray-400">No relations.</p>
            ) : (
              <ul className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
                {relations.map(rel => (
                  <li key={rel.id} className="flex items-center gap-2 px-5 py-2.5 text-sm">
                    {rel.subject ? (
                      <Link href={`/wiki/entities/${rel.subject_entity_id}`}
                        className="font-medium text-gray-800 hover:text-blue-600">{rel.subject.name}</Link>
                    ) : <span className="text-gray-400 text-xs">{rel.subject_entity_id.slice(0, 8)}</span>}
                    <ArrowRight size={12} className="shrink-0 text-gray-400" />
                    <Badge variant="purple">{rel.relation_type}</Badge>
                    <ArrowRight size={12} className="shrink-0 text-gray-400" />
                    {rel.object_entity ? (
                      <Link href={`/wiki/entities/${rel.object_entity_id}`}
                        className="font-medium text-gray-800 hover:text-blue-600">{rel.object_entity.name}</Link>
                    ) : <span className="text-gray-400 text-xs">{rel.object_entity_id.slice(0, 8)}</span>}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
