/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Next-i shkruan vetë AGENTS.md dhe CLAUDE.md në dev; repo-ja
  // i mban vetë udhëzimet e veta.
  agentRules: false,

  // Backend-i punon në një port tjetër. Në prodhim kjo do të
  // zëvendësohej nga një reverse proxy i vetëm.
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  },
};

export default nextConfig;
