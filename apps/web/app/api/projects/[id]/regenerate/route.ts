import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { prisma } from "@/lib/prisma";
import { Octokit } from "octokit";

const ARC42GEN_API_URL = process.env.ARC42GEN_API_URL || "http://localhost:8001";

/**
 * POST /api/projects/[id]/regenerate
 * Generate docs and commit to the docs repo
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

    // Get project with user's GitHub installation
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

    const accessToken = project.user.gitHubInstallation?.accessToken;
    if (!accessToken) {
      return NextResponse.json(
        { error: "GitHub App not installed" },
        { status: 400 }
      );
    }

    // Update status to running
    await prisma.project.update({
      where: { id: projectId },
      data: { docGenStatus: "running" },
    });

    console.log(`Regenerating docs for ${project.name}...`);
    console.log(`Source: ${project.sourceRepoUrl}`);
    console.log(`Docs repo: ${project.githubOwner}/${project.repoName}`);

    // Call arc42gen API with the token for private repos
    const genResponse = await fetch(`${ARC42GEN_API_URL}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_repo_url: project.sourceRepoUrl,
        branch: project.sourceRepoBranch || "main",
        github_token: accessToken,
      }),
    });

    const genResult = await genResponse.json();
    console.log("Arc42gen result:", genResult);

    if (!genResult.success) {
      await prisma.project.update({
        where: { id: projectId },
        data: { docGenStatus: "failed" },
      });
      return NextResponse.json(
        { error: genResult.error || "Doc generation failed" },
        { status: 500 }
      );
    }

    if (Object.keys(genResult.files).length === 0) {
      await prisma.project.update({
        where: { id: projectId },
        data: { docGenStatus: "failed" },
      });
      return NextResponse.json(
        { error: "No documentation files were generated" },
        { status: 500 }
      );
    }

    // Commit files to docs repo
    await commitFilesToRepo({
      accessToken,
      owner: project.githubOwner!,
      repo: project.repoName,
      files: genResult.files,
      message: `docs: regenerate from ${project.sourceRepoOwner}/${project.sourceRepoName}`,
    });

    // Success!
    await prisma.project.update({
      where: { id: projectId },
      data: {
        docGenStatus: "success",
        lastDocGenAt: new Date(),
      },
    });

    console.log(`Docs regenerated successfully for ${project.name}`);

    return NextResponse.json({
      success: true,
      message: "Documentation regenerated and committed",
      filesCommitted: Object.keys(genResult.files).length,
    });

  } catch (error: any) {
    console.error("Regenerate error:", error);
    
    // Try to update status to failed
    try {
      const { id } = await params;
      await prisma.project.update({
        where: { id },
        data: { docGenStatus: "failed" },
      });
    } catch {}

    return NextResponse.json(
      { error: error.message || "Failed to regenerate docs" },
      { status: 500 }
    );
  }
}

/**
 * Commit files to a GitHub repository
 */
async function commitFilesToRepo(options: {
  accessToken: string;
  owner: string;
  repo: string;
  files: Record<string, string>;
  message: string;
}) {
  const { accessToken, owner, repo, files, message } = options;
  const octokit = new Octokit({ auth: accessToken });

  console.log(`Committing ${Object.keys(files).length} files to ${owner}/${repo}`);

  // Get default branch
  const { data: repoData } = await octokit.request("GET /repos/{owner}/{repo}", {
    owner, repo,
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });
  const branch = repoData.default_branch;

  // Get latest commit
  const { data: ref } = await octokit.request("GET /repos/{owner}/{repo}/git/ref/{ref}", {
    owner, repo, ref: `heads/${branch}`,
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });
  const latestCommitSha = ref.object.sha;

  // Get commit tree
  const { data: commit } = await octokit.request("GET /repos/{owner}/{repo}/git/commits/{commit_sha}", {
    owner, repo, commit_sha: latestCommitSha,
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });

  // Create blobs for each file
  const blobs = await Promise.all(
    Object.entries(files).map(async ([path, content]) => {
      const { data: blob } = await octokit.request("POST /repos/{owner}/{repo}/git/blobs", {
        owner, repo,
        content: Buffer.from(content).toString("base64"),
        encoding: "base64",
        headers: { "X-GitHub-Api-Version": "2022-11-28" },
      });
      // Put files in docs/ folder
      return { path: `docs/${path}`, sha: blob.sha };
    })
  );

  // Create tree
  const { data: newTree } = await octokit.request("POST /repos/{owner}/{repo}/git/trees", {
    owner, repo,
    base_tree: commit.tree.sha,
    tree: blobs.map((b) => ({
      path: b.path,
      mode: "100644" as const,
      type: "blob" as const,
      sha: b.sha,
    })),
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });

  // Create commit
  const { data: newCommit } = await octokit.request("POST /repos/{owner}/{repo}/git/commits", {
    owner, repo,
    message,
    tree: newTree.sha,
    parents: [latestCommitSha],
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });

  // Update branch
  await octokit.request("PATCH /repos/{owner}/{repo}/git/refs/{ref}", {
    owner, repo,
    ref: `heads/${branch}`,
    sha: newCommit.sha,
    headers: { "X-GitHub-Api-Version": "2022-11-28" },
  });

  console.log(`Committed to ${owner}/${repo}@${branch}`);
}
