/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export for GitHub Pages.
  // In local dev (`next dev`), output is ignored so hot-reload and rewrites still work.
  output: process.env.NEXT_BUILD_STATIC === 'true' ? 'export' : undefined,

  // GitHub Pages serves the site under /investment-research-database
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',

  trailingSlash: true,

  // <Image> optimisation requires a Node.js server; disable for static export.
  images: { unoptimized: true },

  // Rewrite proxy for local dev (ignored by static export builds).
  async rewrites() {
    if (process.env.NEXT_BUILD_STATIC === 'true') return [];
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
