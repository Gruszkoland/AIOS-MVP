import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    // Proxy API requests to internal services during development
    async rewrites() {
        return [
            {
                source: "/prometheus/:path*",
                destination: `${process.env.PROMETHEUS_URL ?? "http://localhost:9090"}/:path*`,
            },
            {
                source: "/loki/:path*",
                destination: `${process.env.LOKI_URL ?? "http://localhost:3100"}/:path*`,
            },
        ];
    },
};

export default nextConfig;
