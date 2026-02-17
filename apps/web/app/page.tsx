import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { BookOpen, GitBranch, Layers, Terminal, Github } from "lucide-react";
import { GenerateForm } from "@/components/generate/generate-form";
import { SITE } from "@/constants/site";
import { SEO } from "@/constants/seo";
import { CONTENT } from "@/constants/content";

export const metadata: Metadata = {
  title: SEO.pages.home.title,
  description: SEO.pages.home.description,
  alternates: { canonical: "/" },
};

const ICON_MAP = { BookOpen, Layers, GitBranch } as const;

function JsonLd() {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: SITE.name,
    description: SEO.default.description,
    url: SITE.url,
    applicationCategory: "DeveloperApplication",
    operatingSystem: "Cross-platform",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
    logo: `${SITE.url}${SITE.logo.png}`,
    image: `${SITE.url}${SITE.logo.png}`,
    author: {
      "@type": "Organization",
      name: SITE.name,
      url: SITE.url,
      logo: `${SITE.url}${SITE.logo.png}`,
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
    />
  );
}

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <JsonLd />

      {/* Nav */}
      <header className="border-b border-border">
        <div className="container flex h-14 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <Image
              src={SITE.logo.svg}
              alt={`${SITE.name} logo`}
              width={24}
              height={24}
              className="dark:invert"
            />
            <span className="font-semibold text-lg">{SITE.name}</span>
          </Link>
          <nav className="flex items-center gap-4">
            {SITE.nav.links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                {link.label}
              </Link>
            ))}
            {SITE.nav.external.map((link) => (
              <a
                key={link.href}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors inline-flex items-center gap-1"
              >
                <Github className="h-4 w-4" />
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20 sm:py-28">
        <div className="container px-4 max-w-3xl mx-auto text-center space-y-6">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            {CONTENT.hero.heading}
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            {CONTENT.hero.subheading}
          </p>
        </div>
      </section>

      {/* Generate form */}
      <section className="pb-20">
        <div className="container px-4 max-w-2xl mx-auto">
          <GenerateForm />
        </div>
      </section>

      {/* What gets generated */}
      <section className="py-16 border-t border-border">
        <div className="container px-4 max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-10">
            {CONTENT.features.heading}
          </h2>
          <div className="grid gap-6 sm:grid-cols-3">
            {CONTENT.features.cards.map((card) => {
              const Icon = ICON_MAP[card.icon];
              return (
                <div
                  key={card.title}
                  className="rounded-xl border border-border bg-card p-6"
                >
                  <div className="mb-3 rounded-full bg-primary/10 p-2.5 w-fit text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold mb-2">{card.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {card.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CLI quick start */}
      <section className="py-16 border-t border-border">
        <div className="container px-4 max-w-2xl mx-auto">
          <div className="flex items-center gap-2 mb-6">
            <Terminal className="h-5 w-5 text-muted-foreground" />
            <h2 className="text-2xl font-bold">{CONTENT.cli.heading}</h2>
          </div>
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-4 py-2 text-xs text-muted-foreground border-b border-border bg-muted/50 font-mono">
              {CONTENT.cli.terminalLabel}
            </div>
            <pre className="p-4 text-sm overflow-x-auto font-mono leading-relaxed">
              <code>{CONTENT.cli.commands}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-border">
        <div className="container px-4 flex items-center justify-between text-sm text-muted-foreground">
          <Link href="/" className="flex items-center gap-1.5">
            <Image
              src={SITE.logo.svg}
              alt={`${SITE.name} logo`}
              width={16}
              height={16}
              className="dark:invert"
            />
            <span>{SITE.name}</span>
          </Link>
          <div className="flex items-center gap-4">
            {SITE.footer.links.map((link) =>
              link.external ? (
                <a
                  key={link.href}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors"
                >
                  {link.label}
                </a>
              ) : (
                <Link
                  key={link.href}
                  href={link.href}
                  className="hover:text-foreground transition-colors"
                >
                  {link.label}
                </Link>
              )
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}
