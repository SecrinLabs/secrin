import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { prisma } from "@/lib/prisma";
import { Octokit } from "octokit";

interface SourceRepoInput {
  sourceRepoUrl: string;
  branch?: string;
}

/**
 * Parse a GitHub URL to extract owner and repo name
 */
function parseGitHubUrl(url: string): { owner: string; repo: string } | null {
  // Handle various GitHub URL formats:
  // https://github.com/owner/repo
  // https://github.com/owner/repo.git
  // git@github.com:owner/repo.git
  const httpsMatch = url.match(/github\.com\/([^\/]+)\/([^\/\.]+)/);
  if (httpsMatch) {
    return { owner: httpsMatch[1], repo: httpsMatch[2] };
  }

  const sshMatch = url.match(/git@github\.com:([^\/]+)\/([^\/\.]+)/);
  if (sshMatch) {
    return { owner: sshMatch[1], repo: sshMatch[2] };
  }

  return null;
}

/**
 * PUT /api/projects/[id]/source-repo
 * Connect a source repository to a project
 */
export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id: projectId } = await params;
    const { sourceRepoUrl, branch = "main" }: SourceRepoInput = await req.json();

    if (!sourceRepoUrl) {
      return NextResponse.json(
        { error: "Source repository URL is required" },
        { status: 400 }
      );
    }

    // Parse the GitHub URL
    const parsed = parseGitHubUrl(sourceRepoUrl);
    if (!parsed) {
      return NextResponse.json(
        { error: "Invalid GitHub repository URL" },
        { status: 400 }
      );
    }

    // Verify the project belongs to this user
    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId: session.user.id,
      },
    });

    if (!project) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    // Get the user's GitHub installation
    const installation = await prisma.gitHubInstallation.findUnique({
      where: { userId: session.user.id },
    });

    if (!installation?.accessToken) {
      return NextResponse.json(
        { error: "GitHub App not installed. Please install the GitHub App first." },
        { status: 400 }
      );
    }

    // Verify we can access the source repo
    const octokit = new Octokit({ auth: installation.accessToken });

    try {
      await octokit.request("GET /repos/{owner}/{repo}", {
        owner: parsed.owner,
        repo: parsed.repo,
        headers: { "X-GitHub-Api-Version": "2022-11-28" },
      });
    } catch (error: any) {
      if (error.status === 404) {
        return NextResponse.json(
          { error: "Repository not found or not accessible. Make sure the Secrin GitHub App is installed on this repository." },
          { status: 404 }
        );
      }
      throw error;
    }

    // Create a webhook on the source repo to receive PR events
    let webhookId: string | null = null;
    try {
      const webhookSecret = process.env.GITHUB_WEBHOOK_SECRET;
      const appUrl = process.env.NEXTAUTH_URL || process.env.VERCEL_URL;
      
      if (webhookSecret && appUrl) {
        const { data: webhook } = await octokit.request("POST /repos/{owner}/{repo}/hooks", {
          owner: parsed.owner,
          repo: parsed.repo,
          config: {
            url: `${appUrl}/api/webhooks/github`,
            content_type: "json",
            secret: webhookSecret,
          },
          events: ["pull_request"],
          active: true,
          headers: { "X-GitHub-Api-Version": "2022-11-28" },
        });
        webhookId = webhook.id.toString();
      }
    } catch (error: any) {
      // Webhook creation failed - this is okay, we can still proceed
      // Admin hooks require admin access to the repo
      console.warn("Could not create webhook:", error.message);
    }

    // Update the project with source repo info
    const updatedProject = await prisma.project.update({
      where: { id: projectId },
      data: {
        sourceRepoUrl,
        sourceRepoOwner: parsed.owner,
        sourceRepoName: parsed.repo,
        sourceRepoBranch: branch,
        webhookId,
        docGenStatus: "pending",
      },
    });

    return NextResponse.json({
      success: true,
      project: updatedProject,
      webhookCreated: !!webhookId,
    });
  } catch (error: any) {
    console.error("Error connecting source repo:", error);
    return NextResponse.json(
      { error: error.message || "Failed to connect source repository" },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/projects/[id]/source-repo
 * Disconnect the source repository from a project
 */
export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id: projectId } = await params;

    // Verify the project belongs to this user
    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId: session.user.id,
      },
    });

    if (!project) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    // Delete the webhook if it exists
    if (project.webhookId && project.sourceRepoOwner && project.sourceRepoName) {
      const installation = await prisma.gitHubInstallation.findUnique({
        where: { userId: session.user.id },
      });

      if (installation?.accessToken) {
        const octokit = new Octokit({ auth: installation.accessToken });
        try {
          await octokit.request("DELETE /repos/{owner}/{repo}/hooks/{hook_id}", {
            owner: project.sourceRepoOwner,
            repo: project.sourceRepoName,
            hook_id: parseInt(project.webhookId),
            headers: { "X-GitHub-Api-Version": "2022-11-28" },
          });
        } catch (error: any) {
          console.warn("Could not delete webhook:", error.message);
        }
      }
    }

    // Clear source repo fields
    const updatedProject = await prisma.project.update({
      where: { id: projectId },
      data: {
        sourceRepoUrl: null,
        sourceRepoOwner: null,
        sourceRepoName: null,
        sourceRepoBranch: null,
        webhookId: null,
        docGenStatus: null,
      },
    });

    return NextResponse.json({
      success: true,
      project: updatedProject,
    });
  } catch (error: any) {
    console.error("Error disconnecting source repo:", error);
    return NextResponse.json(
      { error: error.message || "Failed to disconnect source repository" },
      { status: 500 }
    );
  }
}

/**
 * GET /api/projects/[id]/source-repo
 * Get source repository connection status
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id: projectId } = await params;

    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId: session.user.id,
      },
      select: {
        id: true,
        sourceRepoUrl: true,
        sourceRepoOwner: true,
        sourceRepoName: true,
        sourceRepoBranch: true,
        webhookId: true,
        lastDocGenAt: true,
        docGenStatus: true,
      },
    });

    if (!project) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    return NextResponse.json({
      connected: !!project.sourceRepoUrl,
      ...project,
    });
  } catch (error: any) {
    console.error("Error getting source repo status:", error);
    return NextResponse.json(
      { error: error.message || "Failed to get source repository status" },
      { status: 500 }
    );
  }
}
