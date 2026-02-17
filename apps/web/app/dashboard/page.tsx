import type { Metadata } from "next";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { redirect } from "next/navigation";
import { DashboardClient } from "@/components/dashboard/dashboard-client";
import { SEO } from "@/constants/seo";

export const metadata: Metadata = {
  title: SEO.pages.dashboard.title,
  description: SEO.pages.dashboard.description,
  robots: { index: false, follow: false },
};

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/auth/login");
  }

  return (
    <DashboardClient
      user={{
        name: session.user?.name,
        email: session.user?.email,
        image: session.user?.image,
        id: session.user?.id,
      }}
    />
  );
}
