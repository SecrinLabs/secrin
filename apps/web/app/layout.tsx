import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { SITE } from "@/constants/site";
import { SEO } from "@/constants/seo";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: SITE.themeColor },
  ],
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: {
    default: SEO.default.title,
    template: `%s — ${SITE.name}`,
  },
  description: SEO.default.description,
  keywords: SEO.default.keywords,
  authors: [{ name: SITE.name, url: SITE.url }],
  creator: SITE.name,
  publisher: SITE.name,
  applicationName: SITE.name,
  generator: "Next.js",
  referrer: "origin-when-cross-origin",
  icons: {
    icon: [
      { url: SITE.logo.icon16, sizes: "16x16", type: "image/png" },
      { url: SITE.logo.icon32, sizes: "32x32", type: "image/png" },
      { url: SITE.logo.icon96, sizes: "96x96", type: "image/png" },
    ],
    shortcut: SITE.logo.favicon,
    apple: [
      { url: "/apple-icon-57x57.png", sizes: "57x57" },
      { url: "/apple-icon-60x60.png", sizes: "60x60" },
      { url: "/apple-icon-72x72.png", sizes: "72x72" },
      { url: "/apple-icon-76x76.png", sizes: "76x76" },
      { url: "/apple-icon-114x114.png", sizes: "114x114" },
      { url: "/apple-icon-120x120.png", sizes: "120x120" },
      { url: "/apple-icon-144x144.png", sizes: "144x144" },
      { url: "/apple-icon-152x152.png", sizes: "152x152" },
      { url: SITE.logo.appleTouchIcon, sizes: "180x180" },
    ],
  },
  manifest: "/manifest.webmanifest",
  openGraph: {
    type: SEO.openGraph.type,
    locale: SEO.openGraph.locale,
    url: SITE.url,
    siteName: SEO.openGraph.siteName,
    title: SEO.default.title,
    description: SEO.default.description,
    images: SEO.openGraph.images,
  },
  twitter: {
    card: SEO.twitter.card,
    site: SEO.twitter.site,
    title: SEO.default.title,
    description: SEO.default.description,
    images: SEO.openGraph.images.map((img) => img.url),
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: SITE.url,
  },
  other: {
    "msapplication-TileColor": SITE.themeColor,
    "msapplication-TileImage": SITE.logo.ms144,
    "msapplication-config": "/browserconfig.xml",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
