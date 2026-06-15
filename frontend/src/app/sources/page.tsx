'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Merged into the Data Hub. Static export disallows server redirect(); use client nav.
export default function SourcesRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace('/data?tab=sources'); }, [router]);
  return null;
}
