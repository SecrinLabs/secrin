import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { Octokit } from "octokit";
import crypto from "crypto";

const ARC42GEN_API_URL = process.env.ARC42GEN_API_URL || "http://localhost:8001";

/**
 * Verify GitHub webhook signature
 */
function verifyGitHubSignature(
  payload: string,
  signature: string | null,
  secret: string
): boolean {
  if (!signature) return false;
  const hmac = crypto.createHmac("sha256", secret);
  const digest = `sha256=${hmac.update(payload).digest("hex")}`;
  try {
    return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest));
  } catch {
    return false;
  }
}

/**
 * POST /api/webhooks/github
 * 
 * Flow:
 * 1. Receive PR merged event
 * 2. Call arc42gen API to generate docs
 * 3. Commit generated docs to the docs repo
 * 4. Docs app automatically shows updated docs (reads from GitHub)
 */
export async function POST(req: NextRequest) {
  try {
    const webhookSecret = process.env.GITHUB_WEBHOOK_SECRET;
    if (!webhookSecret) {
      console.error("GITHUB_WEBHOOK_SECRET not configured");
      return NextResponse.json({ error: "Webhook not configured" }, { status: 500 });
    }

    const rawBody = await req.text();
    const signature = req.headers.get("x-hub-signature-256");
    const event = req.headers.get("x-github-event");

    if (!verifyGitHubSignature(rawBody, signature, webhookSecret)) {
      return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
    }

    const payload = JSON.parse(rawBody);
    console.log(`GitHub webhook: ${event}`, { action: payload.action, repo: payload.repository?.full_name });

    // Handle ping
    if (event === "ping") {
      return NextResponse.json({ success: true, message: "pong" });
    }

    // Only handle merged PRs
    if (event !== "pull_request" || payload.action !== "closed" || !payload.pull_request?.merged) {
      return NextResponse.json({ success: true, message: "Ignored" });
    }

    const targetBranch = payload.pull_request.base.ref;
    const repoOwner = payload.repository.owner.login;
    const repoName = payload.repository.name;
    const sourceRepoUrl = payload.repository.html_url;

    // Find projects tracking this repo/branch
    const projects = await prisma.project.findMany({
      where: {
        sourceRepoOwner: repoOwner,
        sourceRepoName: repoName,
        sourceRepoBranch: targetBranch,
      },
      include: {
        user: {
          include: {
            gitHubInstallation: true,
          },
        },
      },
    });

    if (projects.length === 0) {
      console.log(`No projects tracking ${repoOwner}/${repoName}:${targetBranch}`);
      return NextResponse.json({ success: true, message: "No matching projects" });
    }

    // Process each project
    for (const project of projects) {
      try {
        console.log(`Processing project: ${project.name}`);
        
        // Update status
        await prisma.project.update({
          where: { id: project.id },
          data: { docGenStatus: "running" },
        });

        // Call arc42gen API
        const genResponse = await fetch(`${ARC42GEN_API_URL}/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_repo_url: sourceRepoUrl,
            branch: targetBranch,
          }),
        });

        const genResult = await genResponse.json();

        if (!genResult.success || Object.keys(genResult.files).length === 0) {
          console.error(`Doc generation failed for ${project.name}:`, genResult.error);
          await prisma.project.update({
            where: { id: project.id },
            data: { docGenStatus: "failed" },
          });
          continue;
        }

        // Commit to docs repo
        const accessToken = project.user.gitHubInstallation?.accessToken;
        if (!accessToken) {
          console.error(`No access token for project ${project.name}`);
          await prisma.project.update({
            where: { id: project.id },
            data: { docGenStatus: "failed" },
          });
          continue;
        }

        await commitFilesToRepo({
          accessToken,
          owner: project.githubOwner!,
          repo: project.repoName,
          files: genResult.files,
          message: `docs: auto-update from ${repoOwner}/${repoName}`,
        });

        // Success!
        await prisma.project.update({
          where: { id: project.id },
          data: {
            docGenStatus: "success",
            lastDocGenAt: new Date(),
          },
        });

        console.log(`Docs updated for project: ${project.name}`);

      } catch (error: any) {
        console.error(`Error processing project ${project.name}:`, error);
        await prisma.project.update({
          where: { id: project.id },
          data: { docGenStatus: "failed" },
        });
      }
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error("Webhook error:", error);
    return NextResponse.json({ error: "Webhook failed" }, { status: 500 });
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
}
