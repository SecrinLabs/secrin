import { getProjectBySlug } from "@/lib/api";
import { fetchGitHubDocs, fetchGitHubDoc } from "@/lib/github";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { Metadata } from "next";

interface PageProps {
  params: Promise<{
    project: string;
    slug?: string[];
  }>;
}

export default async function ProjectDocsPage({ params }: PageProps) {
  const { project: projectSlug, slug } = await params;
  const docSlug = slug?.[0] || "index";

  // 1. Find project via main app API
  const project = await getProjectBySlug(projectSlug);

  if (!project || !project.githubOwner) {
    notFound();
  }

  // 2. Fetch all docs for sidebar
  const allDocs = await fetchGitHubDocs(project.githubOwner, project.repoName);

  // 3. Fetch the specific doc
  const doc = await fetchGitHubDoc(
    project.githubOwner,
    project.repoName,
    docSlug
  );

  if (!doc && docSlug !== "index") {
    notFound();
  }

  // If no doc and it's the index, show onboarding
  if (!doc && allDocs.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto py-16 px-4">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Welcome to {project.name} Docs
          </h1>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">
              Get Started
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Your documentation site is ready! Create a <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">docs</code> folder 
              in your repository and add markdown files to get started.
            </p>
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Repository:</p>
              <a 
                href={project.repoUrl || "#"} 
                className="text-blue-600 dark:text-blue-400 hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                {project.githubOwner}/{project.repoName}
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 border-r border-gray-200 dark:border-gray-800 min-h-screen p-4 hidden md:block">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4">
            {project.name}
          </h2>
          <nav className="space-y-1">
            {allDocs.map((d) => (
              <a
                key={d.slug}
                href={`/${projectSlug}/${d.slug}`}
                className={`block px-3 py-2 rounded-md text-sm ${
                  d.slug === docSlug
                    ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                {d.title}
              </a>
            ))}
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 max-w-4xl px-8 py-12">
          {doc ? (
            <article className="prose dark:prose-invert max-w-none">
              <ReactMarkdown>{doc.content}</ReactMarkdown>
            </article>
          ) : (
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
                {project.name} Documentation
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mb-8">
                Select a page from the sidebar to get started.
              </p>
              <ul className="space-y-2">
                {allDocs.map((d) => (
                  <li key={d.slug}>
                    <a
                      href={`/${projectSlug}/${d.slug}`}
                      className="text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {d.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { project: projectSlug, slug } = await params;
  const docSlug = slug?.[0] || "index";

  const project = await getProjectBySlug(projectSlug);

  if (!project || !project.githubOwner) {
    return { title: "Not Found" };
  }

  const doc = await fetchGitHubDoc(
    project.githubOwner,
    project.repoName,
    docSlug
  );

  return {
    title: doc ? `${doc.title} | ${project.name}` : project.name,
    description: project.description || `Documentation for ${project.name}`,
  };
}
