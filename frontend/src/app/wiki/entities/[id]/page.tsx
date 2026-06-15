// Server component: generates static params at build time, delegates UI to client component.
import WikiEntityClient from './WikiEntityClient';
import type { Entity } from '@/lib/types';

// Pre-generate one HTML shell per entity so GitHub Pages can serve the path.
// `output: export` requires a non-empty result for a dynamic route, so when the
// backend is unavailable at build time we still emit a placeholder shell; real
// entity pages remain reachable via in-app client-side navigation.
const PLACEHOLDER = [{ id: 'placeholder' }];

export async function generateStaticParams() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return PLACEHOLDER;
  try {
    const res = await fetch(`${apiUrl}/api/entities?limit=500`, { cache: 'no-store' });
    if (!res.ok) return PLACEHOLDER;
    const entities: Entity[] = await res.json();
    return entities.length ? entities.map((e) => ({ id: e.id })) : PLACEHOLDER;
  } catch {
    return PLACEHOLDER;
  }
}

export default function WikiEntityPage({ params }: { params: { id: string } }) {
  return <WikiEntityClient id={params.id} />;
}
