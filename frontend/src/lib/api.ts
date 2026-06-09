// Central API client.
// - In the browser: calls go through the Next.js rewrite proxy (/api → backend).
// - On the server (RSC / server components): relative URLs have no origin, so we
//   target the backend directly via NEXT_PUBLIC_API_URL.

function resolveUrl(path: string): string {
  if (typeof window === 'undefined') {
    const origin = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return `${origin}/api${path}`;
  }
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
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => fetcher<T>(path),
  post: <T>(path: string, body: unknown) =>
    fetcher<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    fetcher<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (path: string) => fetcher<void>(path, { method: 'DELETE' }),
};
