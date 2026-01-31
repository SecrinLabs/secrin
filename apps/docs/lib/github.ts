import { Octokit } from "octokit";

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

interface GitHubFile {
  name: string;
  path: string;
  content: string;
  sha: string;
}

interface DocsPage {
  slug: string;
  title: string;
  content: string;
  path: string;
}

/**
 * Fetch all markdown files from a GitHub repo's docs folder
 */
export async function fetchGitHubDocs(
  owner: string,
  repo: string,
  docsPath: string = "docs"
): Promise<DocsPage[]> {
  try {
    // Get list of files in the docs directory
    const { data: contents } = await octokit.request(
      "GET /repos/{owner}/{repo}/contents/{path}",
      {
        owner,
        repo,
        path: docsPath,
        headers: {
          "X-GitHub-Api-Version": "2022-11-28",
        },
      }
    );

    if (!Array.isArray(contents)) {
      return [];
    }

    // Filter for markdown files
    const mdFiles = contents.filter(
      (file: { type: string; name: string }) =>
        file.type === "file" && 
        (file.name.endsWith(".md") || file.name.endsWith(".mdx"))
    );

    // Fetch content for each file
    const pages: DocsPage[] = await Promise.all(
      mdFiles.map(async (file: { path: string; name: string }) => {
        const { data: fileData } = await octokit.request(
          "GET /repos/{owner}/{repo}/contents/{path}",
          {
            owner,
            repo,
            path: file.path,
            headers: {
              "X-GitHub-Api-Version": "2022-11-28",
            },
          }
        );

        // Decode base64 content
        const content = Buffer.from(
          (fileData as { content: string }).content,
          "base64"
        ).toString("utf-8");

        // Extract title from first heading or filename
        const titleMatch = content.match(/^#\s+(.+)$/m);
        const title = titleMatch
          ? titleMatch[1]
          : file.name.replace(/\.(md|mdx)$/, "");

        // Generate slug from filename
        const slug = file.name.replace(/\.(md|mdx)$/, "");

        return {
          slug,
          title,
          content,
          path: file.path,
        };
      })
    );

    return pages;
  } catch (error: any) {
    if (error.status === 404) {
      // Repo or docs folder doesn't exist
      return [];
    }
    throw error;
  }
}

/**
 * Fetch a single markdown file from GitHub
 */
export async function fetchGitHubDoc(
  owner: string,
  repo: string,
  slug: string,
  docsPath: string = "docs"
): Promise<DocsPage | null> {
  const filePaths = [`${docsPath}/${slug}.md`, `${docsPath}/${slug}.mdx`];

  for (const filePath of filePaths) {
    try {
      const { data: fileData } = await octokit.request(
        "GET /repos/{owner}/{repo}/contents/{path}",
        {
          owner,
          repo,
          path: filePath,
          headers: {
            "X-GitHub-Api-Version": "2022-11-28",
          },
        }
      );

      const content = Buffer.from(
        (fileData as { content: string }).content,
        "base64"
      ).toString("utf-8");

      const titleMatch = content.match(/^#\s+(.+)$/m);
      const title = titleMatch ? titleMatch[1] : slug;

      return {
        slug,
        title,
        content,
        path: filePath,
      };
    } catch (error: any) {
      if (error.status !== 404) {
        throw error;
      }
      // Try next file path
    }
  }

  return null;
}
