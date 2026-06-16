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

export const api = {
  get: <T>(path: string) => fetcher<T>(path),
  post: <T>(path: string, body: unknown) =>
    fetcher<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    fetcher<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path: string) => fetcher<void>(path, { method: 'DELETE' }),
  // Absolute URL for file downloads (CSV export etc.), usable as an <a href>.
  url: (path: string) => resolveUrl(path),
};
