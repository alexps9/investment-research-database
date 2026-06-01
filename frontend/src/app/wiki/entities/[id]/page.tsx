import { api } from '@/lib/api';
import type { WikiEntityProfile } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Link from 'next/link';
import { ArrowRight, ExternalLink, ArrowLeft } from 'lucide-react';
import { notFound } from 'next/navigation';

async function getWiki(id: string): Promise<WikiEntityProfile | null> {
  try { return await api.get<WikiEntityProfile>(`/wiki/entities/${id}`); }
  catch { return null; }
}

const typeColor: Record<string, 'blue' | 'green' | 'purple' | 'yellow' | 'default'> = {
  person: 'blue', organization: 'green', model: 'purple', method: 'yellow', topic: 'default',
};

export default async function WikiEntityPage({ params }: { params: { id: string } }) {
  const profile = await getWiki(params.id);
  if (!profile) notFound();

  const { entity, aliases, related_signals, outgoing_relations, incoming_relations, related_entities } = profile;

  return (
    <div className="p-8 max-w-4xl">
      <Link href="/wiki" className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-blue-600">
        <ArrowLeft size={14} /> Back to Wiki
      </Link>

      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold text-gray-900">{entity.name}</h1>
          <Badge variant={typeColor[entity.entity_type] ?? 'default'} className="text-sm px-3 py-1">
            {entity.entity_type}
          </Badge>
        </div>
        {entity.description && <p className="text-gray-600">{entity.description}</p>}
        {entity.homepage_url && (
          <a href={entity.homepage_url} target="_blank" rel="noreferrer"
            className="mt-1 flex items-center gap-1 text-sm text-blue-600 hover:underline">
            {entity.homepage_url} <ExternalLink size={12} />
          </a>
        )}
        {aliases.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            <span className="text-xs text-gray-400 mr-1">Also known as:</span>
            {aliases.map(a => <Badge key={a.id} variant="gray">{a.alias}</Badge>)}
          </div>
        )}
      </div>

      <div className="space-y-6">
        {outgoing_relations.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Outgoing Relations ({outgoing_relations.length})</CardTitle></CardHeader>
            <CardContent className="p-0">
              <ul className="divide-y divide-gray-100">
                {outgoing_relations.map(rel => (
                  <li key={rel.id} className="flex items-center gap-3 px-5 py-3">
                    <span className="font-medium text-gray-900 text-sm">{entity.name}</span>
                    <Badge variant="purple">{rel.relation_type}</Badge>
                    <ArrowRight size={14} className="text-gray-400" />
                    {rel.object_entity ? (
                      <Link href={`/wiki/entities/${rel.object_entity_id}`}
                        className="text-sm text-blue-600 hover:underline">{rel.object_entity.name}</Link>
                    ) : <span className="text-sm text-gray-500">{rel.object_entity_id}</span>}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {incoming_relations.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Incoming Relations ({incoming_relations.length})</CardTitle></CardHeader>
            <CardContent className="p-0">
              <ul className="divide-y divide-gray-100">
                {incoming_relations.map(rel => (
                  <li key={rel.id} className="flex items-center gap-3 px-5 py-3">
                    {rel.subject ? (
                      <Link href={`/wiki/entities/${rel.subject_entity_id}`}
                        className="text-sm text-blue-600 hover:underline">{rel.subject.name}</Link>
                    ) : <span className="text-sm text-gray-500">{rel.subject_entity_id}</span>}
                    <ArrowRight size={14} className="text-gray-400" />
                    <Badge variant="purple">{rel.relation_type}</Badge>
                    <ArrowRight size={14} className="text-gray-400" />
                    <span className="font-medium text-gray-900 text-sm">{entity.name}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {related_signals.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Related Signals ({related_signals.length})</CardTitle></CardHeader>
            <CardContent className="p-0">
              <ul className="divide-y divide-gray-100">
                {related_signals.map(sig => (
                  <li key={sig.id} className="px-5 py-3">
                    <div className="flex items-start gap-2">
                      <Badge>{sig.signal_type}</Badge>
                      <a href={sig.url} target="_blank" rel="noreferrer"
                        className="flex items-start gap-1 text-sm font-medium text-gray-900 hover:text-blue-600">
                        {sig.title} <ExternalLink size={11} className="mt-0.5 shrink-0" />
                      </a>
                    </div>
                    {sig.analysis?.tldr && <p className="mt-1 text-xs text-gray-500 pl-1">{sig.analysis.tldr}</p>}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {related_entities.length > 0 && (
          <Card>
            <CardHeader><CardTitle>Related Entities</CardTitle></CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {related_entities.map(ent => (
                  <Link key={ent.id} href={`/wiki/entities/${ent.id}`}
                    className="flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-sm hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 transition-colors">
                    <Badge variant={typeColor[ent.entity_type] ?? 'default'} className="text-xs">{ent.entity_type}</Badge>
                    {ent.name}
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
