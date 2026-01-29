"use client";

import { useState } from "react";
import { Plus, FolderKanban } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CreateProjectWizard } from "@/components/projects/create-project-wizard";
import { LogoutButton } from "@/components/logout-button";
import { Project, CreateProjectResponse } from "@/types/project";

interface DashboardClientProps {
  user: {
    name?: string | null;
    email?: string | null;
    image?: string | null;
    id?: string;
  };
}

export function DashboardClient({ user }: DashboardClientProps) {
  const [showWizard, setShowWizard] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);

  const handleProjectCreated = (response: CreateProjectResponse) => {
    setProjects((prev) => [...prev, response.data.project]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <FolderKanban className="h-6 w-6 text-primary" />
            <span className="font-semibold text-lg">Secrin</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {user.image && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={user.image}
                  alt={user.name || "User"}
                  className="h-8 w-8 rounded-full border"
                />
              )}
              <span className="text-sm font-medium hidden sm:inline">
                {user.name || "User"}
              </span>
            </div>
            <LogoutButton />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
            <p className="text-muted-foreground mt-1">
              Manage your projects and connected repositories
            </p>
          </div>
          <Button onClick={() => setShowWizard(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            New Project
          </Button>
        </div>

        {projects.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <div className="rounded-full bg-muted p-4 mb-4">
                <FolderKanban className="h-8 w-8 text-muted-foreground" />
              </div>
              <CardTitle className="text-xl mb-2">No projects yet</CardTitle>
              <CardDescription className="text-center max-w-sm mb-6">
                Get started by creating your first project. We&apos;ll set up a
                repository in your GitHub account.
              </CardDescription>
              <Button onClick={() => setShowWizard(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                Create Your First Project
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Card key={project.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="text-lg">{project.name}</CardTitle>
                  {project.description && (
                    <CardDescription>{project.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="font-mono">{project.repoName}</span>
                    {project.repoUrl && (
                      <a
                        href={project.repoUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        View
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Project Creation Wizard Modal */}
      {showWizard && (
        <CreateProjectWizard
          onClose={() => setShowWizard(false)}
          onSuccess={handleProjectCreated}
        />
      )}
    </div>
  );
}
