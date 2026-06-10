'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// server-side redirect() is not supported by next `output: 'export'`.
// Use a client-side effect instead.
export default function RootPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);
  return null;
}
