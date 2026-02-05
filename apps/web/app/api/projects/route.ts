import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { prisma } from "@/lib/prisma";
import { getValidAccessToken } from "@/lib/github-token";
import { Octokit } from "octokit";

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

    // Get a valid access token (will auto-refresh if expired)
    const tokenResult = await getValidAccessToken(session.user.id);
    
    if (tokenResult.error) {
      return NextResponse.json({ error: tokenResult.error }, { status: 400 });
    }

    // Use the access token (ghu_*) to authenticate
    const octokit = new Octokit({ auth: tokenResult.accessToken });

    // Create Repo in user's account
    const repoName = sanitizeRepoName(name);
    const { data: createdRepo } = await octokit.request("POST /user/repos", {
      name: repoName,
      description: description || `Project: ${name}`,
      private: true,
      auto_init: true,
      headers: {
        "X-GitHub-Api-Version": "2022-11-28",
      },
    });

    // Save to DB
    const project = await prisma.project.create({
      data: {
        name,
        slug: repoName, // URL-friendly unique identifier
        description,
        repoName: createdRepo.name,
        repoUrl: createdRepo.html_url,
        githubOwner: createdRepo.owner.login, // GitHub username who owns the repo
        userId: session.user.id,
      },
    });

    return NextResponse.json({ success: true, data: { project, repoUrl: createdRepo.html_url } });
  } catch (error: any) {
    console.error("GitHub API Error:", error.response?.data || error.message);
    return NextResponse.json({ error: error.message || "Failed to create repo" }, { status: 500 });
  }
}

/**
 * GET /api/projects
 * Get all projects for the current user
 */
export async function GET() {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const projects = await prisma.project.findMany({
      where: { userId: session.user.id },
      orderBy: { createdAt: "desc" },
    });

    return NextResponse.json({ projects });
  } catch (error: any) {
    console.error("Error fetching projects:", error);
    return NextResponse.json({ error: "Failed to fetch projects" }, { status: 500 });
  }
}
