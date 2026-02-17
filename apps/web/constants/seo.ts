import { SITE } from "./site";

export const SEO = {
  default: {
    title: "Secrin — AI-Powered Documentation for Any Codebase",
    description:
      "Generate Arc42 architecture docs, C4 diagrams, and Diataxis guides from any GitHub repository in minutes. Open source and self-hostable.",
    keywords: [
      "documentation generator",
      "arc42",
      "c4 diagrams",
      "diataxis",
      "architecture documentation",
      "code documentation",
      "AI documentation",
      "developer tools",
      "open source",
      "codebase analysis",
      "software architecture",
      "engineering knowledge",
      "automated docs",
    ],
  },
  openGraph: {
    type: "website" as const,
    locale: "en_US",
    siteName: SITE.name,
    images: [
      {
        url: `${SITE.url}/secrin_logo.png`,
        width: 192,
        height: 192,
        alt: "Secrin Logo",
        type: "image/png",
      },
    ],
  },
  twitter: {
    card: "summary" as const,
    site: "@secrinlabs",
  },
  pages: {
    home: {
      title: "Secrin — Generate Documentation for Any Codebase",
      description:
        "Paste a GitHub repo URL. Get Arc42 architecture docs, C4 diagrams, and Diataxis guides in minutes. Open source and self-hostable.",
    },
    dashboard: {
      title: "Dashboard — Secrin",
      description:
        "Manage your projects and connected repositories. Generate and regenerate documentation for your codebases.",
    },
    login: {
      title: "Sign In — Secrin",
      description:
        "Sign in to your Secrin account to manage projects and generate documentation.",
    },
  },
};
