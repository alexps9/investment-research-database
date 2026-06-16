/** @type {import('next').NextConfig} */

// GitHub Pages needs a basePath + trailing slashes to serve the static export
// from a subpath. Vercel serves at the root and proxies /api/* via vercel.json,
// where trailing-slash redirects would break the API proxy — so only enable
// trailingSlash for the GitHub Pages build (detected via the base path).
const isGithubPages = !!process.env.NEXT_PUBLIC_BASE_PATH;

const nextConfig = {
  // Static export for GitHub Pages.
  // In local dev (`next dev`), output is ignored so hot-reload and rewrites still work.
  output: process.env.NEXT_BUILD_STATIC === 'true' ? 'export' : undefined,

  // GitHub Pages serves the site under /investment-research-database
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',

  trailingSlash: isGithubPages,

  // <Image> optimisation requires a Node.js server; disable for static export.
  images: { unoptimized: true },

  // Rewrite proxy for local dev only. In production the API is reached either
  // directly via NEXT_PUBLIC_API_URL (GitHub Pages static export) or through
  // Vercel's edge rewrite in vercel.json (which proxies /api/* to the Tencent
  // backend so the HTTPS frontend can talk to the HTTP backend without
  // mixed-content errors). Returning [] here avoids a broken localhost rewrite
  // leaking into a Vercel server build.
  async rewrites() {
    if (process.env.NODE_ENV !== 'development') return [];
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
