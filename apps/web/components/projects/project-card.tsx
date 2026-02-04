"use client";

import { useState } from "react";
import { Github, Link2, ExternalLink, BookOpen, MoreVertical, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Project } from "@/types/project";
import { ConnectSourceRepoModal } from "./connect-source-repo-modal";
import { DocGenStatusBadge, SourceRepoInfo } from "./docgen-status";

interface ProjectCardProps {
  project: Project;
  onUpdate: (project: Project) => void;
}

export function ProjectCard({ project, onUpdate }: ProjectCardProps) {
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleTriggerRegenerate = async () => {
    if (!project.sourceRepoUrl) return;

    setIsRegenerating(true);
    try {
      const response = await fetch(`/api/projects/${project.id}/regenerate`, {
        method: "POST",
      });

      if (response.ok) {
        const data = await response.json();
        onUpdate({ ...project, docGenStatus: "pending" });
      }
    } catch (error) {
      console.error("Failed to trigger regeneration:", error);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect the source repository?")) {
      return;
    }

    try {
      const response = await fetch(`/api/projects/${project.id}/source-repo`, {
        method: "DELETE",
      });

      if (response.ok) {
        const data = await response.json();
        onUpdate(data.project);
      }
    } catch (error) {
      console.error("Failed to disconnect source repo:", error);
    }
  };

  return (
    <>
      <Card className="hover:shadow-md transition-shadow group">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-lg flex items-center gap-2">
                {project.name}
                {project.docGenStatus && (
                  <DocGenStatusBadge
                    status={project.docGenStatus}
                    lastDocGenAt={project.lastDocGenAt}
                  />
                )}
              </CardTitle>
              {project.description && (
                <CardDescription className="line-clamp-2">
                  {project.description}
                </CardDescription>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Docs Repository */}
          <div className="flex items-center gap-2 text-sm">
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Docs:</span>
            <span className="font-mono">{project.repoName}</span>
            {project.repoUrl && (
              <a
                href={project.repoUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/80"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>

          {/* Source Repository */}
          {project.sourceRepoUrl ? (
            <div className="space-y-2">
              <SourceRepoInfo
                sourceRepoUrl={project.sourceRepoUrl}
                sourceRepoOwner={project.sourceRepoOwner}
                sourceRepoName={project.sourceRepoName}
                sourceRepoBranch={project.sourceRepoBranch}
                docGenStatus={project.docGenStatus}
                lastDocGenAt={project.lastDocGenAt}
                onTriggerRegenerate={handleTriggerRegenerate}
                isRegenerating={isRegenerating}
              />
              <button
                onClick={handleDisconnect}
                className="text-xs text-muted-foreground hover:text-destructive transition-colors"
              >
                Disconnect source repo
              </button>
            </div>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowConnectModal(true)}
              className="gap-2 w-full"
            >
              <Link2 className="h-4 w-4" />
              Connect Source Repository
            </Button>
          )}

          {/* View Docs Link */}
          {project.slug && (
            <a
              href={`${process.env.NEXT_PUBLIC_DOCS_URL || "http://localhost:3001"}/${project.slug}`}
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <Button variant="default" size="sm" className="w-full gap-2">
                <BookOpen className="h-4 w-4" />
                View Documentation
              </Button>
            </a>
          )}
        </CardContent>
      </Card>

      {showConnectModal && (
        <ConnectSourceRepoModal
          project={project}
          onClose={() => setShowConnectModal(false)}
          onSuccess={(updatedProject) => {
            onUpdate(updatedProject);
            setShowConnectModal(false);
          }}
        />
      )}
    </>
  );
}
