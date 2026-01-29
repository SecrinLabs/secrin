import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { prisma } from "@/lib/prisma";
import { Octokit } from "octokit";
import { createAppAuth } from "@octokit/auth-app";

const sanitizeRepoName = (name: string) =>
  name
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "") || `project-${Date.now()}`;

export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { name, description } = await req.json();
    if (!name) {
      return NextResponse.json({ error: "Project name is required" }, { status: 400 });
    }

    const installation = await prisma.gitHubInstallation.findUnique({
      where: { userId: session.user.id },
    });
    if (!installation) {
      return NextResponse.json({ error: "GitHub App not installed" }, { status: 400 });
    }

    // 1. Authenticate
    const appId = process.env.GITHUB_APP_ID!;
    const privateKey = Buffer.from(process.env.GITHUB_APP_PRIVATE_KEY!, "base64").toString("utf-8");

    const { token } = await createAppAuth({ appId, privateKey })({
      type: "installation",
      installationId: installation.installationId,
    });
    const octokit = new Octokit({ auth: token });

    // 2. DEBUG: Verify Token Permissions
    const { headers } = await octokit.request("HEAD /");
    console.log("Token Scopes:", headers["x-oauth-scopes"]);

    // 3. Create Repo (Personal Account)
    const repoName = sanitizeRepoName(name);
    const { data: createdRepo } = await octokit.request("POST /user/repos", {
      name: repoName,
      description: description || `Project: ${name}`,
      private: true,
      auto_init: true,
    });

    // 4. Save to DB
    const project = await prisma.project.create({
      data: {
        name,
        description,
        repoName: createdRepo.name,
        repoUrl: createdRepo.html_url,
        userId: session.user.id,
      },
    });

    return NextResponse.json({ success: true, data: { project, repoUrl: createdRepo.html_url } });
  } catch (error: any) {
    console.error("GitHub API Error:", error.response?.data || error.message);
    return NextResponse.json({ error: error.message || "Failed to create repo" }, { status: 500 });
  }
}

