"use client";

import { useState, useEffect } from "react";
import { Button } from "@workspace/ui/components/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@workspace/ui/components/dialog";
import { Input } from "@workspace/ui/components/input";
import { Label } from "@workspace/ui/components/label";
import { Github, Eye, EyeOff } from "lucide-react";
import { GithubConfig } from "@workspace/ui/types/Integration";

export function GitHubIntegrationModal({
  open,
  onClose,
  config,
}: {
  open: boolean;
  onClose: () => void;
  config: GithubConfig;
}) {
  const [username, setUsername] = useState("");
  const [token, setToken] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [error, setError] = useState("");
  const [showToken, setShowToken] = useState(false);

  // Initialize form with config data when modal opens
  useEffect(() => {
    if (open && config) {
      setUsername(config.username || "");
      setToken(config.token || "");
      setRepoUrl(config.repoUrl || "");
      setError("");
    }
  }, [open, config]);

  const isValid =
    username &&
    token.length >= 10 &&
    /^https:\/\/github.com\/.+\/.+/.test(repoUrl);

  async function handleConnect() {
    if (!isValid) {
      setError("Please fill all fields correctly.");
      return;
    }
    setError("");

    try {
      const response = await fetch(
        "http://localhost:8000/api/integration/update",
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: "github", // or the relevant integration name
            is_connected: true, // or the actual state
            config: {
              username,
              token,
              repoUrl,
            },
          }),
        },
      );
      if (!response.ok) {
        const data = await response.json();
        setError(data.detail || "Failed to update integration.");
        return;
      }
      onClose();
    } catch (err) {
      setError("Network error.");
    }

    onClose();
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-800">
              <Github className="h-5 w-5 text-gray-700 dark:text-gray-300" />
            </div>
            <div>
              <DialogTitle>Connect GitHub Repository</DialogTitle>
              <DialogDescription className="mt-1">
                To fetch commit history and code context, DevSecrin needs access
                to your GitHub account. Generate a Personal Access Token with
                repo and read:user permissions.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="username">GitHub Username</Label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="octocat"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="token">Personal Access Token</Label>
            <div className="relative">
              <Input
                id="token"
                type={showToken ? "text" : "password"}
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowToken(!showToken)}
              >
                {showToken ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="repo-url">Repository URL</Label>
            <Input
              id="repo-url"
              type="url"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
            />
          </div>

          {/* {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )} */}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleConnect} disabled={!isValid}>
            Connect Repository
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
