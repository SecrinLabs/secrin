"use client";

import { useEffect, useState } from "react";
import { Zap, Settings, Play } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card";
import { Switch } from "@workspace/ui/components/switch";
import { GitHubIntegrationModal } from "@workspace/ui/components/integrations/GitHubIntegrationModal";
import { DocumentationIntegrationModal } from "@workspace/ui/components/integrations/DocumentationIntegrationModal";
import { LocalRepoIntegrationModal } from "@workspace/ui/components/integrations/LocalRepoIntegrationModal";
import { useStartScraper } from "@workspace/ui/hooks/scraper/useScraper";
import { useEnableEmbedder } from "@workspace/ui/hooks/embed/useEnableEmbedder";
import { useLoadIntegration } from "@workspace/ui/hooks/misc/useLoadIntegration";
import { Integration, IntegrationUIMap } from "@workspace/ui/types/Integration";

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
  const { mutate: startScraping, isPending } = useStartScraper();
  const { mutate: changeIntegrationStatus } = useEnableEmbedder();
  const { mutate: loadIntegration } = useLoadIntegration();
  const [integrations, setIntegrations] = useState<Integration[]>([]);

  useEffect(() => {
    loadIntegration(undefined, {
      onSuccess: (data) => {
        console.log(data);
        setIntegrations(data);
      },
      onError: (err) => {
        console.error("Integration fetch failed", err);
      },
    });
  }, []);

  const toggleIntegration = (name: string) => {
    setIntegrations((prev) =>
      prev.map((integration) =>
        integration.name === name
          ? { ...integration, is_connected: !integration.is_connected }
          : integration
      )
    );
    changeIntegrationStatus(name); // Call the mutation when toggling
  };

  const handleStartEmbedding = async () => {
    const enabledIntegrations = integrations.filter((i) => i.is_connected);

    if (enabledIntegrations.length === 0) {
      toast.error(
        "Please enable at least one integration before starting embedding."
      );
      return;
    }

    try {
      toast.info(
        `Starting embedding for ${enabledIntegrations.length} integration(s)...`
      );

      // Start scraping for all enabled integrations
      for (const integration of enabledIntegrations) {
        await new Promise((resolve) => {
          startScraping(integration.id, {
            onSuccess: () => {
              toast.success(`${integration.name} embedding started!`);
              resolve(true);
            },
            onError: (error) => {
              toast.error(
                `${integration.name} embedding failed: ${error.message}`
              );
              resolve(false);
            },
          });
        });
      }

      toast.success("All embeddings completed successfully!");
    } catch (error) {
      toast.error("Embedding process failed. Please try again.");
    }
  };

  const enabledCount = integrations.filter((i) => i.is_connected).length;

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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {integrations.map((integration) => {
          const ui = IntegrationUIMap[integration.name];
          return (
            <Card
              key={integration.id}
              className={`group hover:shadow-lg transition-all duration-300 border-2 hover:border-primary/20 relative overflow-hidden ${
                !integration.is_connected ? "opacity-60" : ""
              }`}
            >
              <div className={`absolute inset-0 opacity-5 ${ui.color}`} />
              <CardHeader className="relative">
                <div className="flex items-start justify-between mb-4">
                  <div
                    className={`p-3 rounded-xl ${ui.color} text-white shadow-lg`}
                  >
                    <ui.icon className="w-6 h-6" />
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={integration.is_connected}
                      onCheckedChange={() =>
                        toggleIntegration(integration.name)
                      }
                    />
                    <span className="text-xs text-muted-foreground">
                      {integration.is_connected ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                </div>
                <CardTitle className="text-xl font-semibold group-hover:text-primary transition-colors">
                  {integration.name}
                </CardTitle>
                <CardDescription className="text-sm leading-relaxed">
                  {ui.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="relative space-y-3">
                <Button
                  variant="default"
                  className="w-full font-medium"
                  disabled={!integration.is_connected}
                  onClick={() => {
                    if (integration.name === "github") setOpen("github");
                    else if (integration.name === "sitemap") setOpen("docs");
                    else if (integration.name === "gitlocal") setOpen("local");
                  }}
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Configure
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Single Start Embedding Button */}
      <div className="text-center mb-8">
        <div className="mb-4">
          <p className="text-muted-foreground mb-2">
            {enabledCount} integration{enabledCount !== 1 ? "s" : ""} enabled
          </p>
        </div>
        <Button
          onClick={handleStartEmbedding}
          disabled={isPending || enabledCount === 0}
          size="lg"
          className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-3 text-lg font-medium"
        >
          {isPending ? (
            <>
              <Zap className="w-5 h-5 mr-2 animate-pulse" />
              Embedding in progress...
            </>
          ) : (
            <>
              <Play className="w-5 h-5 mr-2" />
              Start Data Collection & Embedding
            </>
          )}
        </Button>
      </div>

      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-muted rounded-full text-sm text-muted-foreground">
          <Play className="w-4 h-4" />
          More integrations coming soon
        </div>
      </div>
    </div>
  );
}
