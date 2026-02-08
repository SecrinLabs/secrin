"use client";

import { useState } from "react";
import { X, Github, Loader2, CheckCircle, AlertCircle, Link2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Project } from "@/types/project";

interface ConnectSourceRepoModalProps {
  project: Project;
  onClose: () => void;
  onSuccess: (updatedProject: Project) => void;
}

export function ConnectSourceRepoModal({
  project,
  onClose,
  onSuccess,
}: ConnectSourceRepoModalProps) {
  const [sourceRepoUrl, setSourceRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    if (!sourceRepoUrl.trim()) {
      setError("Please enter a repository URL");
      return;
    }

    // Basic URL validation
    if (!sourceRepoUrl.includes("github.com")) {
      setError("Please enter a valid GitHub repository URL");
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const response = await fetch(`/api/projects/${project.id}/source-repo`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sourceRepoUrl: sourceRepoUrl.trim(),
          branch: branch.trim() || "main",
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to connect repository");
      }

      onSuccess(data.project);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md animate-in fade-in zoom-in-95 duration-200">
        <CardHeader className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-4 top-4"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <Link2 className="h-5 w-5 text-primary" />
            </div>
            <CardTitle>Connect Source Repository</CardTitle>
          </div>
          <CardDescription>
            Connect a code repository to automatically generate documentation when
            changes are merged.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="sourceRepoUrl">GitHub Repository URL</Label>
            <div className="relative">
              <Github className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="sourceRepoUrl"
                placeholder="https://github.com/owner/repository"
                value={sourceRepoUrl}
                onChange={(e) => setSourceRepoUrl(e.target.value)}
                className="pl-10"
                disabled={isConnecting}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Make sure the Secrin GitHub App is installed on this repository.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="branch">Branch to Watch</Label>
            <Input
              id="branch"
              placeholder="main"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              disabled={isConnecting}
            />
            <p className="text-xs text-muted-foreground">
              Docs will regenerate when PRs are merged to this branch.
            </p>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 rounded-lg p-3">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isConnecting}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleConnect}
              disabled={isConnecting || !sourceRepoUrl.trim()}
              className="flex-1 gap-2"
            >
              {isConnecting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Connect
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
