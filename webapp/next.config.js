/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NEXT_BUILD_STATIC === 'true' ? 'export' : undefined,
  images: { unoptimized: true },
  async rewrites() {
    if (process.env.NODE_ENV !== 'development') return [];
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
