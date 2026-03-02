import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output for Docker deployment
  output: "standalone",

  // Enable gzip/brotli compression
  compress: true,

  // Tree-shake heavy packages — only bundle used exports
  experimental: {
    optimizePackageImports: [
      "recharts",
      "lucide-react",
      "radix-ui",
      "react-hook-form",
      "zod",
    ],
  },

  // Reduce JS sent to client
  reactStrictMode: true,

  // Optimized image handling
  images: {
    formats: ["image/avif", "image/webp"],
  },

  // Custom headers for static asset caching
  async headers() {
    return [
      {
        source: "/:all*(svg|jpg|png|webp|avif|woff2)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
