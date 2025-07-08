"use client";

import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card";
import { Badge } from "@workspace/ui/components/badge";
import { GitHubIntegrationModal } from "@workspace/ui/components/integrations/GitHubIntegrationModal";
import { DocumentationIntegrationModal } from "@workspace/ui/components/integrations/DocumentationIntegrationModal";
import { LocalRepoIntegrationModal } from "@workspace/ui/components/integrations/LocalRepoIntegrationModal";
import {
  Github,
  BookOpen,
  FolderOpen,
  Zap,
  Settings,
  Play,
} from "lucide-react";

export type IntegrationModalType = null | "github" | "docs" | "local";

export interface IntegrationModalsProps {
  open: IntegrationModalType;
  setOpen: (type: IntegrationModalType) => void;
}

export function IntegrationModals({ open, setOpen }: IntegrationModalsProps) {
  return (
    <>
      <GitHubIntegrationModal
        open={open === "github"}
        onClose={() => setOpen(null)}
      />
      <DocumentationIntegrationModal
        open={open === "docs"}
        onClose={() => setOpen(null)}
      />
      <LocalRepoIntegrationModal
        open={open === "local"}
        onClose={() => setOpen(null)}
      />
    </>
  );
}

export function IntegrationButtons({
  setOpen,
}: {
  setOpen: (type: IntegrationModalType) => void;
}) {
  const handleStartEmbedding = async (integrationType: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/scraper/start-scraper/${integrationType}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ type: integrationType }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to start embedding");
      }

      // Handle success
      console.log("Embedding started for:", integrationType);
    } catch (error) {
      console.error("Error starting embedding:", error);
    }
  };

  const integrations = [
    {
      id: "github",
      title: "GitHub Repository",
      description:
        "Connect your GitHub repositories to sync code and documentation",
      icon: Github,
      color: "bg-gradient-to-br from-gray-900 to-gray-700",
      badge: "Popular",
      badgeVariant: "default" as const,
    },
    {
      id: "sitemap",
      title: "Documentation",
      description: "Configure and manage your project documentation settings",
      icon: BookOpen,
      color: "bg-gradient-to-br from-blue-600 to-blue-800",
      badge: "Essential",
      badgeVariant: "secondary" as const,
    },
    {
      id: "gitlocal",
      title: "Local Repository",
      description: "Add local repositories from your development environment",
      icon: FolderOpen,
      color: "bg-gradient-to-br from-emerald-600 to-emerald-800",
      badge: "Quick Setup",
      badgeVariant: "outline" as const,
    },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold tracking-tight mb-2">
          Connect Your Integrations
        </h2>
        <p className="text-muted-foreground text-lg">
          Choose from our available integrations to enhance your workflow
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.map((integration) => {
          const IconComponent = integration.icon;
          return (
            <Card
              key={integration.id}
              className="group hover:shadow-lg transition-all duration-300 border-2 hover:border-primary/20 relative overflow-hidden"
            >
              <div
                className={`absolute inset-0 opacity-5 ${integration.color}`}
              />

              <CardHeader className="relative">
                <div className="flex items-start justify-between mb-4">
                  <div
                    className={`p-3 rounded-xl ${integration.color} text-white shadow-lg`}
                  >
                    <IconComponent className="w-6 h-6" />
                  </div>
                  <Badge variant={integration.badgeVariant} className="text-xs">
                    {integration.badge}
                  </Badge>
                </div>

                <CardTitle className="text-xl font-semibold group-hover:text-primary transition-colors">
                  {integration.title}
                </CardTitle>
                <CardDescription className="text-sm leading-relaxed">
                  {integration.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="relative space-y-3">
                <Button
                  variant="default"
                  className="w-full font-medium"
                  onClick={() =>
                    setOpen(integration.id as IntegrationModalType)
                  }
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Configure
                </Button>

                <Button
                  variant="secondary"
                  className="w-full font-medium group/btn hover:bg-primary hover:text-primary-foreground transition-all"
                  onClick={() => handleStartEmbedding(integration.id)}
                >
                  <Zap className="w-4 h-4 mr-2 group-hover/btn:animate-pulse" />
                  Start Embedding
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-12 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-muted rounded-full text-sm text-muted-foreground">
          <Play className="w-4 h-4" />
          More integrations coming soon
        </div>
      </div>
    </div>
  );
}
