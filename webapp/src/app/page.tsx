'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import SearchHome from '@/components/SearchHome';
import SessionWorkspace from '@/components/SessionWorkspace';

type View = 'report' | 'trajectory' | 'people' | 'industry';

function Home() {
  const sp = useSearchParams();
  const id = sp.get('id');
  const viewParam = sp.get('view');
  const view: View =
    viewParam === 'trajectory' || viewParam === 'people' || viewParam === 'industry'
      ? viewParam
      : 'report';

  // Everything lives on the index route via query params, so the static export
  // (nginx falls back to /index.html) serves session views on hard load AND
  // client navigation — dynamic `/s/[id]` routes break under `output: export`.
  if (id) return <SessionWorkspace id={id} view={view} />;
  return <SearchHome />;
}

export default function Page() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center text-slate-400">加载中…</div>}>
      <Home />
    </Suspense>
  );
}
