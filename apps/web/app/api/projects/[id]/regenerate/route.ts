import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { prisma } from "@/lib/prisma";
import { getValidAccessTokenFromInstallation } from "@/lib/github-token";

const ARC42GEN_API_URL = process.env.ARC42GEN_API_URL || "http://localhost:8001";

function log(msg: string) {
  console.log(`[regenerate] ${new Date().toISOString().slice(11, 19)} ${msg}`);
}

function logError(msg: string, err?: any) {
  console.error(`[regenerate] ${new Date().toISOString().slice(11, 19)} ${msg}`);
  if (err) console.error(err);
}

/**
 * POST /api/projects/[id]/regenerate
 * Submit a doc generation job (returns immediately with job_id)
 */
export async function POST(
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
      include: {
        user: {
          include: {
            gitHubInstallation: true,
          },
        },
      },
    });

    if (!project) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    if (!project.sourceRepoUrl) {
      return NextResponse.json(
        { error: "No source repository connected" },
        { status: 400 }
      );
    }

    // Get a valid access token
    log(`Getting access token for installation...`);
    const tokenResult = await getValidAccessTokenFromInstallation(project.user.gitHubInstallation);
    if (tokenResult.error) {
      logError(`Token error: ${tokenResult.error}`);
      return NextResponse.json(
        { error: tokenResult.error },
        { status: 400 }
      );
    }
    const accessToken = tokenResult.accessToken!;
    log(`Token obtained successfully`);

    log(`========================================`);
    log(`Submitting doc generation job`);
    log(`  Project: ${project.name}`);
    log(`  Source: ${project.sourceRepoUrl}`);
    log(`  Docs repo: ${project.githubOwner}/${project.repoName}`);
    log(`  API URL: ${ARC42GEN_API_URL}`);
    log(`========================================`);

    // Submit job to arc42gen API (returns instantly)
    const jobResponse = await fetch(`${ARC42GEN_API_URL}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_repo_url: project.sourceRepoUrl,
        branch: project.sourceRepoBranch || "main",
        github_token: accessToken,
        owner: project.githubOwner,
        repo_name: project.repoName,
        source_owner: project.sourceRepoOwner,
        source_name: project.sourceRepoName,
        project_id: projectId,
      }),
      signal: AbortSignal.timeout(10_000), // 10s — should be instant
    });

    if (!jobResponse.ok) {
      const errText = await jobResponse.text();
      logError(`Job submission failed: ${jobResponse.status} ${errText}`);
      return NextResponse.json(
        { error: "Failed to submit generation job" },
        { status: 500 }
      );
    }

    const jobResult = await jobResponse.json();
    log(`Job submitted: ${jobResult.job_id}`);

    // Store job_id and set status to running
    await prisma.project.update({
      where: { id: projectId },
      data: {
        docGenStatus: "running",
        docGenJobId: jobResult.job_id,
      },
    });

    return NextResponse.json(
      {
        success: true,
        job_id: jobResult.job_id,
        message: "Documentation generation job submitted",
      },
      { status: 202 }
    );

  } catch (error: any) {
    logError(`Failed to submit job: ${error.message}`, error);

    // Try to update status to failed
    try {
      const { id } = await params;
      await prisma.project.update({
        where: { id },
        data: { docGenStatus: "failed" },
      });
    } catch {}

    return NextResponse.json(
      { error: error.message || "Failed to submit generation job" },
      { status: 500 }
    );
  }
}
