'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Merged into the Data Hub. Static export disallows server redirect(); use client nav.
export default function SignalsRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace('/data?tab=signals'); }, [router]);
  return null;
}
