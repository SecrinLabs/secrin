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
import { Alert, AlertDescription } from "@workspace/ui/components/alert";
import { FolderOpen, AlertCircle, Scan } from "lucide-react";
import { GitLocalConfig } from "@workspace/ui/types/Integration.js";

export function LocalRepoIntegrationModal({
  open,
  onClose,
  config,
}: {
  open: boolean;
  onClose: () => void;
  config: GitLocalConfig;
}) {
  const [localPath, setLocalPath] = useState("");
  const [projectName, setProjectName] = useState("");
  const [error, setError] = useState("");

  // Initialize form with config data when modal opens
  useEffect(() => {
    if (open && config) {
      setLocalPath(config.localPath || config.repo_path || "");
      setProjectName(config.projectName || "");
      setError("");
    }
  }, [open, config]);

  const isValid = localPath.length > 0 && projectName.length > 0;

  async function handleSave() {
    if (!isValid) {
      setError("Please fill all fields.");
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
            name: "gitlocal", // or the relevant integration name
            is_connected: true, // or the actual state
            config: {
              repo_path: localPath,
              localPath,
              projectName,
            },
          }),
        }
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
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900">
              <FolderOpen className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <DialogTitle>Add Local Code Repository</DialogTitle>
              <DialogDescription className="mt-1">
                Point DevSecrin to a local codebase directory. This will enable
                offline analysis and context extraction.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="local-path">Local Path</Label>
            <Input
              id="local-path"
              type="text"
              value={localPath}
              onChange={(e) => setLocalPath(e.target.value)}
              placeholder="/Users/yourname/project"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="project-name">Project Name</Label>
            <Input
              id="project-name"
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="My Project"
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
          <Button onClick={handleSave} disabled={!isValid}>
            <Scan className="mr-2 h-4 w-4" />
            Scan & Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
