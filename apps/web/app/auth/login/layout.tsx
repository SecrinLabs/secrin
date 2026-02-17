import type { Metadata } from "next";
import { SEO } from "@/constants/seo";

export const metadata: Metadata = {
  title: SEO.pages.login.title,
  description: SEO.pages.login.description,
  robots: { index: false, follow: false },
};

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
