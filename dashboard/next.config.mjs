/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // Configure basePath if your GitHub Pages repo is named "lab-5"
  // If you are deploying to a user/org root (username.github.io), remove this line.
  basePath: process.env.GITHUB_ACTIONS ? "/lab-5" : "",
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    unoptimized: true,
  }
};

export default nextConfig;
