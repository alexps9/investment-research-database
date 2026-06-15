'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Wiki search merged into Explore. Entity wiki pages remain at /wiki/entities/[id].
export default function WikiRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace('/explore'); }, [router]);
  return null;
}
