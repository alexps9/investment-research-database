function resolveUrl(path: string): string {
  const origin = process.env.NEXT_PUBLIC_API_URL;
  if (origin) return `${origin}/api${path}`;
  return `/api${path}`;
}

async function fetcher<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(resolveUrl(path), {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    cache: 'no-store',
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

const GET_TTL_MS = 30_000;
const getCache = new Map<string, { ts: number; data: unknown }>();

export const api = {
  get: <T>(path: string, opts?: { cache?: boolean }) => {
    if (opts?.cache === false) return fetcher<T>(path);
    const hit = getCache.get(path);
    if (hit && Date.now() - hit.ts < GET_TTL_MS) return Promise.resolve(hit.data as T);
    return fetcher<T>(path).then((data) => {
      getCache.set(path, { ts: Date.now(), data });
      return data;
    });
  },
  post: <T>(path: string, body: unknown) => {
    getCache.clear();
    return fetcher<T>(path, { method: 'POST', body: JSON.stringify(body) });
  },
  delete: (path: string) => {
    getCache.clear();
    return fetcher<void>(path, { method: 'DELETE' });
  },
  invalidate: () => getCache.clear(),
};
