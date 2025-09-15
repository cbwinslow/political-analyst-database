/**
 * @type {import('next').NextConfig}
 *
 * This is a professional, feature-rich Next.js configuration for Project Sentinel.
 * It includes:
 * - Security Headers: Protects against common web vulnerabilities.
 * - Image Optimization: Securely allows and optimizes images from trusted government domains.
 * - API Proxy (Rewrites): Simplifies API calls during development by proxying requests to the backend.
 * - Build Analyzer: Provides a tool to visualize and analyze the size of JavaScript bundles.
 * - PWA Support: Enables Progressive Web App capabilities for offline access and an app-like feel.
 */

// Tool for analyzing the final JS bundle size.
// To use, run `ANALYZE=true npm run build` in the /frontend directory.
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

// PWA configuration
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
});

const nextConfig = {
  // Enables React's Strict Mode, which helps identify potential problems in an application.
  reactStrictMode: true,

  // Use the SWC compiler for minification, which is much faster than the default (Terser).
  swcMinify: true,

  // Configuration for Next.js Image Optimization
  images: {
    // Specifies the formats that can be optimized.
    formats: ['image/avif', 'image/webp'],
    // Defines a list of trusted remote domains from which images can be sourced.
    // This is a security measure to prevent loading images from untrusted sources.
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.house.gov',
      },
      {
        protocol: 'https',
        hostname: '**.senate.gov',
      },
      {
        protocol: 'https',
        hostname: '**.whitehouse.gov',
      },
      {
        protocol: 'https',
        hostname: '**.cia.gov',
      },
      {
        protocol: 'https',
        hostname: '**.fbi.gov',
      },
       {
        protocol: 'https',
        hostname: 'upload.wikimedia.org', // For public figure photos
      },
      {
        protocol: 'https',
        hostname: 'placehold.co', // For placeholder images during development
      },
    ],
  },

  // Asynchronous function to configure custom HTTP headers.
  // These headers enhance application security.
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          // Enforces secure connections (HTTPS)
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          // Prevents the browser from interpreting files as something other than their declared content type.
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          // Prevents the site from being rendered in an iframe, protecting against clickjacking.
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
           // Enables the browser's built-in XSS protection.
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },

  // Asynchronous function to configure URL rewrites.
  // This acts as a proxy, making API calls cleaner and avoiding CORS issues in development.
  async rewrites() {
    return [
      {
        // Proxies requests from /api/... in the frontend to the Kong API gateway.
        source: '/api/:path*',
        // In a Docker environment, the destination is the service name 'kong'.
        // For local development outside Docker, you might change this to http://localhost:8000.
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

// We wrap our configuration with the plugins.
// The order can matter, so we compose them.
module.exports = withPWA(withBundleAnalyzer(nextConfig));

