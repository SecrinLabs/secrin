"use client";

import { Button } from "@workspace/ui/components/button";
import { GitHubIntegrationModal } from "@workspace/ui/components/integrations/GitHubIntegrationModal";
import { DocumentationIntegrationModal } from "@workspace/ui/components/integrations/DocumentationIntegrationModal";
import { LocalRepoIntegrationModal } from "@workspace/ui/components/integrations/LocalRepoIntegrationModal";

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
  return (
    <div className="flex flex-col gap-4 w-full max-w-sm">
      <Button variant="default" onClick={() => setOpen("github")}>
        Connect GitHub
      </Button>
      <Button variant="secondary" onClick={() => setOpen("docs")}>
        Configure Documentation
      </Button>
      <Button variant="default" onClick={() => setOpen("local")}>
        Add Local Repository
      </Button>
    </div>
  );
}
