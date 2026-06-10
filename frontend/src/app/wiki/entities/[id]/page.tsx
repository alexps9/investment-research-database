// Server component: generates static params at build time, delegates UI to client component.
import WikiEntityClient from './WikiEntityClient';
import type { Entity } from '@/lib/types';

// Pre-generate one HTML shell per entity so GitHub Pages can serve the path.
// If the backend is unavailable at build time the array is empty; pages are
// still accessible via client-side navigation (the JS bundle handles routing).
export async function generateStaticParams() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return [];
  try {
    const res = await fetch(`${apiUrl}/api/entities?limit=500`, { cache: 'no-store' });
    if (!res.ok) return [];
    const entities: Entity[] = await res.json();
    return entities.map((e) => ({ id: e.id }));
  } catch {
    return [];
  }
}

export default function WikiEntityPage({ params }: { params: { id: string } }) {
  return <WikiEntityClient id={params.id} />;
}
