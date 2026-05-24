import type { NextConfig } from "next";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";
const isProd = process.env.NODE_ENV === "production";

// In production: drop unsafe-eval (only needed by Next.js dev HMR).
// Add api.visaiapp.com to connect-src — the API base in production is an absolute URL
// (NEXT_PUBLIC_API_URL=https://api.visaiapp.com) and must be whitelisted explicitly.
const scriptSrc = isProd
  ? "script-src 'self' 'unsafe-inline'"
  : "script-src 'self' 'unsafe-inline' 'unsafe-eval'";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      scriptSrc,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob: https:",
      "font-src 'self'",
      // api.visaiapp.com = production API; keep 'self' for same-origin dev proxy
      "connect-src 'self' https://api.visaiapp.com https://api.stripe.com",
      // Stripe 3DS / SCA can use additional frame origins
      "frame-src https://js.stripe.com https://hooks.stripe.com https://m.stripe.network",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  allowedDevOrigins: [],
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${BACKEND}/api/v1/:path*`,
      },
      {
        source: "/barber-refs/:path*",
        destination: `${BACKEND}/barber-refs/:path*`,
      },
    ];
  },
};

export default nextConfig;
