export const SITE = {
  name: "Secrin",
  tagline: "AI-powered documentation for any codebase",
  url: "https://secrinlabs.com",
  github: "https://github.com/secrinlabs/secrin",
  logo: {
    svg: "/secrin_logo.svg",
    png: "/secrin_logo.png",
    favicon: "/favicon.ico",
    appleTouchIcon: "/apple-icon-180x180.png",
    icon16: "/favicon-16x16.png",
    icon32: "/favicon-32x32.png",
    icon96: "/favicon-96x96.png",
    android192: "/android-icon-192x192.png",
    ms144: "/ms-icon-144x144.png",
  },
  themeColor: "#111827",
  nav: {
    links: [
      { label: "Dashboard", href: "/dashboard" },
    ],
    external: [
      { label: "GitHub", href: "https://github.com/secrinlabs/secrin" },
    ],
  },
  footer: {
    links: [
      { label: "Sign in", href: "/auth/login", external: false },
      { label: "GitHub", href: "https://github.com/secrinlabs/secrin", external: true },
    ],
  },
} as const;
