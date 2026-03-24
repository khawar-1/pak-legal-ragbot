/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: "/api/:path*",
          destination: "http://localhost:8000/api/:path*",
        },
        {
          source: "/docs",
          destination: "http://localhost:8000/docs",
        },
        {
          source: "/openapi.json", 
          destination: "http://localhost:8000/openapi.json",
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
