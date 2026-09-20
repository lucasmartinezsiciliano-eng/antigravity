import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Las fichas de los portales traen imagenes de dominios que cambian a menudo,
  // asi que las servimos con <img> normal y no con next/image.
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
