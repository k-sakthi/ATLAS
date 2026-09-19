/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In production on Vercel, this should point to the Railway backend URL
    const apiUrl = process.env.API_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${apiUrl}/health`,
      }
    ]
  },
};

export default nextConfig;
