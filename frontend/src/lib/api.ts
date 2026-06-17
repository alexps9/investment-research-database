// Central API client.
//
// Resolution strategy:
//   - NEXT_PUBLIC_API_URL is set  → call backend directly (production / static export)
//   - NEXT_PUBLIC_API_URL not set  → use relative /api/* (Next.js dev-server rewrite proxy)

function resolveUrl(path: string): string {
  const origin = process.env.NEXT_PUBLIC_API_URL;
  if (origin) return `${origin}/api${path}`;
  return `/api${path}`;
}

export const TOKEN_KEY = 'hh_token';

function authHeader(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const token = window.localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetcher<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(resolveUrl(path), {
    headers: { 'Content-Type': 'application/json', ...authHeader(), ...init?.headers },
    cache: 'no-store',
    ...init,
  });
  if (res.status === 401 && typeof window !== 'undefined') {
    // Token missing/expired — drop it and let the auth gate take over.
    window.localStorage.removeItem(TOKEN_KEY);
    window.dispatchEvent(new Event('hh-auth-expired'));
  }
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  // 204 No Content (e.g. DELETE) or an empty body has no JSON to parse.
  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return undefined as T;
  }
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

// ── Client-side GET cache ────────────────────────────────────────────────────
// The DB sits a region away from the backend (~120ms/round-trip) and the API is
// reached over a high-latency cross-border link, so re-fetching the same data on
// every page navigation is the dominant source of perceived slowness. We keep a
// short-lived in-memory cache so navigating back to a page is instant, dedupe
// concurrent identical requests, and drop the whole cache on any write so edits
// show up immediately. Pass `{ cache: false }` for polling / always-fresh reads.
const GET_TTL_MS = 60_000;
type CacheEntry = { ts: number; data: unknown };
const getCache = new Map<string, CacheEntry>();
const inflight = new Map<string, Promise<unknown>>();

function invalidateCache(): void {
  getCache.clear();
  inflight.clear();
}

if (typeof window !== 'undefined') {
  // A different user (or re-login) must not see another session's cached data.
  window.addEventListener('hh-auth-expired', invalidateCache);
}

function cachedGet<T>(path: string, opts?: { cache?: boolean }): Promise<T> {
  if (opts?.cache === false) return fetcher<T>(path);

  const hit = getCache.get(path);
  if (hit && Date.now() - hit.ts < GET_TTL_MS) {
    return Promise.resolve(hit.data as T);
  }
  const pending = inflight.get(path);
  if (pending) return pending as Promise<T>;

  const p = fetcher<T>(path)
    .then((data) => {
      getCache.set(path, { ts: Date.now(), data });
      inflight.delete(path);
      return data;
    })
    .catch((err) => {
      inflight.delete(path);
      throw err;
    });
  inflight.set(path, p as Promise<unknown>);
  return p;
}

export const api = {
  get: <T>(path: string, opts?: { cache?: boolean }) => cachedGet<T>(path, opts),
  post: <T>(path: string, body: unknown) =>
    fetcher<T>(path, { method: 'POST', body: JSON.stringify(body) }).then((r) => {
      invalidateCache();
      return r;
    }),
  patch: <T>(path: string, body: unknown) =>
    fetcher<T>(path, { method: 'PATCH', body: JSON.stringify(body) }).then((r) => {
      invalidateCache();
      return r;
    }),
  delete: (path: string) =>
    fetcher<void>(path, { method: 'DELETE' }).then(() => {
      invalidateCache();
    }),
  // Drop the GET cache manually (e.g. an explicit "refresh" button).
  invalidate: invalidateCache,
  // Absolute URL for file downloads (CSV export etc.), usable as an <a href>.
  url: (path: string) => resolveUrl(path),
};
