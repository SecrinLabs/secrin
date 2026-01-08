import { createProject, getProjects, deleteProject } from "@/lib/registry";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import Link from "next/link";
import { revalidatePath } from "next/cache";
import { ArrowLeft, BookOpen, FolderOpen, Trash2 } from "lucide-react";

export default async function DocsAdminPage() {
  const projects = await getProjects();

  // Server Action to add a project
  async function addProjectAction(formData: FormData) {
    "use server";
    const name = formData.get("name") as string;
    const slug = formData.get("slug") as string;
    const localPath = formData.get("path") as string;

    if (!name || !slug || !localPath) {
      throw new Error("All fields are required");
    }

    // Validate slug format
    const slugRegex = /^[a-z0-9-]+$/;
    if (!slugRegex.test(slug)) {
      throw new Error("Slug must be lowercase alphanumeric with hyphens only");
    }

    await createProject({ name, slug, localPath });
    revalidatePath("/docs-admin");
  }

  // Server Action to delete a project
  async function deleteProjectAction(formData: FormData) {
    "use server";
    const slug = formData.get("slug") as string;
    await deleteProject(slug);
    revalidatePath("/docs-admin");
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto p-8 space-y-8">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Documentation Admin
            </h1>
            <p className="text-muted-foreground">
              Manage your documentation sources
            </p>
          </div>
        </div>

        {/* Add Project Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FolderOpen className="h-5 w-5" />
              Add Documentation Source
            </CardTitle>
            <CardDescription>
              Register a local folder containing Markdown or Markdoc files
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form action={addProjectAction} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Project Name</label>
                  <Input name="name" placeholder="My API Docs" required />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Slug (URL path)</label>
                  <Input
                    name="slug"
                    placeholder="api-v1"
                    pattern="^[a-z0-9-]+$"
                    title="Lowercase letters, numbers, and hyphens only"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Local Path</label>
                  <Input
                    name="path"
                    placeholder="/Users/jenil/projects/docs"
                    required
                  />
                </div>
              </div>
              <Button type="submit">Add Documentation Source</Button>
            </form>
          </CardContent>
        </Card>

        {/* Project List */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Registered Projects</h2>
          {projects.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-10 text-center">
                <BookOpen className="h-12 w-12 text-muted-foreground/50 mb-4" />
                <p className="text-muted-foreground">
                  No documentation sources registered yet.
                </p>
                <p className="text-sm text-muted-foreground">
                  Add a local folder above to get started.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projects.map((project) => (
                <Card
                  key={project.slug}
                  className="group relative overflow-hidden"
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">
                          {project.name}
                        </CardTitle>
                        <CardDescription className="flex items-center gap-1 mt-1">
                          <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                            /{project.slug}
                          </code>
                        </CardDescription>
                      </div>
                      <form action={deleteProjectAction}>
                        <input type="hidden" name="slug" value={project.slug} />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                          type="submit"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </form>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <p className="text-xs text-muted-foreground font-mono truncate mb-4">
                      {project.localPath}
                    </p>
                    <Link href={`/docs/${project.slug}`}>
                      <Button variant="outline" size="sm" className="w-full">
                        <BookOpen className="h-4 w-4 mr-2" />
                        View Documentation
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
