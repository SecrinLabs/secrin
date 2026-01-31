const MAIN_APP_URL = process.env.MAIN_APP_URL || "http://localhost:3000";

interface Project {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  repoName: string;
  repoUrl: string | null;
  githubOwner: string | null;
}

/**
 * Fetch project details from the main app API
 */
export async function getProjectBySlug(slug: string): Promise<Project | null> {
  try {
    const response = await fetch(`${MAIN_APP_URL}/api/projects/by-slug/${slug}`, {
      cache: "no-store", // Always fetch fresh data
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data.project;
  } catch (error) {
    console.error("Error fetching project:", error);
    return null;
  }
}
