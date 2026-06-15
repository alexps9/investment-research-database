'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Merged into Explore (keyword + semantic + AI Q&A).
export default function AskRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace('/explore'); }, [router]);
  return null;
}
