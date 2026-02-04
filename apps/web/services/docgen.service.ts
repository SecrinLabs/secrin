import { Octokit } from "octokit";
import { prisma } from "@/lib/prisma";

interface CommitDocsOptions {
  projectId: string;
  accessToken: string;
  docsRepo: {
    owner: string;
    name: string;
  };
  files: Array<{
    path: string;
    content: string;
  }>;
}

/**
 * Commit generated documentation files to the docs repository
 * The docs app will automatically pick them up since it reads from GitHub
 */
export async function commitDocsToRepo(options: CommitDocsOptions): Promise<void> {
  const { projectId, accessToken, docsRepo, files } = options;

  const octokit = new Octokit({ auth: accessToken });

  try {
    // Update status
    await prisma.project.update({
      where: { id: projectId },
      data: { docGenStatus: "running" },
    });

    // Get the default branch
    const { data: repo } = await octokit.request("GET /repos/{owner}/{repo}", {
      owner: docsRepo.owner,
      repo: docsRepo.name,
      headers: { "X-GitHub-Api-Version": "2022-11-28" },
    });

    const branch = repo.default_branch;

    // Get the latest commit SHA
    const { data: ref } = await octokit.request("GET /repos/{owner}/{repo}/git/ref/{ref}", {
      owner: docsRepo.owner,
      repo: docsRepo.name,
      ref: `heads/${branch}`,
      headers: { "X-GitHub-Api-Version": "2022-11-28" },
    });

    const latestCommitSha = ref.object.sha;

    // Get the tree of the latest commit
    const { data: commit } = await octokit.request("GET /repos/{owner}/{repo}/git/commits/{commit_sha}", {
      owner: docsRepo.owner,
      repo: docsRepo.name,
      commit_sha: latestCommitSha,
      headers: { "X-GitHub-Api-Version": "2022-11-28" },
    });

    // Create blobs for each file
    const blobs = await Promise.all(
      files.map(async (file) => {
        const { data: blob } = await octokit.request("POST /repos/{owner}/{repo}/git/blobs", {
          owner: docsRepo.owner,
          repo: docsRepo.name,
          content: Buffer.from(file.content).toString("base64"),
          encoding: "base64",
          headers: { "X-GitHub-Api-Version": "2022-11-28" },
        });
        return { path: file.path, sha: blob.sha };
      })
    );

    // Create a new tree with the files
    const { data: newTree } = await octokit.request("POST /repos/{owner}/{repo}/git/trees", {
      owner: docsRepo.owner,
      repo: docsRepo.name,
      base_tree: commit.tree.sha,
      tree: blobs.map((blob) => ({
        path: blob.path,
        mode: "100644" as const,
        type: "blob" as const,
        sha: blob.sha,
      })),
      headers: { "X-GitHub-Api-Version": "2022-11-28" },
    });

    // Create a new commit
    const { data: newCommit } = await octokit.request("POST /repos/{owner}/{repo}/git/commits", {
      owner: docsRepo.owner,
      repo: docsRepo.name,
      message: "docs: update generated documentation",
      tree: newTree.sha,
      parents: [latestCommitSha],
      headers: { "X-GitHub-Api-Version": "2022-11-28" },
    });

    // Update the branch reference
    await octokit.request("PATCH /repos/{owner}/{repo}/git/refs/{ref}", {
      owner: docsRepo.owner,
      repo: docsRepo.name,
      ref: `heads/${branch}`,
      sha: newCommit.sha,
      headers: { "X-GitHub-Api-Version": "2022-11-28" },
    });

    // Update status to success
    await prisma.project.update({
      where: { id: projectId },
      data: {
        docGenStatus: "success",
        lastDocGenAt: new Date(),
      },
    });

    console.log(`Docs committed to ${docsRepo.owner}/${docsRepo.name}`);
  } catch (error: any) {
    console.error("Failed to commit docs:", error);
    await prisma.project.update({
      where: { id: projectId },
      data: { docGenStatus: "failed" },
    });
    throw error;
  }
}

/**
 * Update doc generation status
 */
export async function updateDocGenStatus(
  projectId: string,
  status: "pending" | "running" | "success" | "failed"
): Promise<void> {
  await prisma.project.update({
    where: { id: projectId },
    data: {
      docGenStatus: status,
      lastDocGenAt: status === "success" ? new Date() : undefined,
    },
  });
}
