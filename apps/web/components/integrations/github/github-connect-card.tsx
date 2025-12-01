"use client";

import { useState } from "react";
import { Github, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GITHUB_CONFIG } from "@/constants/integrations/github";
import { GitHubService } from "@/services/integrations/github.service";

export function GitHubConnectCard() {
  const [repoUrl, setRepoUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<{
    type: "success" | "error" | null;
    message: string;
  }>({ type: null, message: "" });

  const handleConnect = async () => {
    if (!repoUrl) {
      setStatus({ type: "error", message: GITHUB_CONFIG.TEXT.ERROR_EMPTY_URL });
      return;
    }

    setIsLoading(true);
    setStatus({ type: null, message: "" });

    try {
      const response = await GitHubService.connectRepository(repoUrl);

      if (response.success) {
        setStatus({
          type: "success",
          message: GITHUB_CONFIG.TEXT.SUCCESS_MESSAGE(response.data.full_name),
        });
        setRepoUrl("");
      } else {
        setStatus({
          type: "error",
          message: response.message || GITHUB_CONFIG.TEXT.ERROR_GENERIC,
        });
      }
    } catch (error) {
      setStatus({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : GITHUB_CONFIG.TEXT.ERROR_GENERIC,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Github className="h-6 w-6" />
          <CardTitle>{GITHUB_CONFIG.TEXT.TITLE}</CardTitle>
        </div>
        <CardDescription>{GITHUB_CONFIG.TEXT.DESCRIPTION}</CardDescription>
      </CardHeader>
      <CardContent className="flex-1">
        <div className="grid w-full items-center gap-4">
          <div className="flex flex-col space-y-1.5">
            <Label htmlFor="github-repo-url">
              {GITHUB_CONFIG.TEXT.INPUT_LABEL}
            </Label>
            <Input
              id="github-repo-url"
              placeholder={GITHUB_CONFIG.TEXT.INPUT_PLACEHOLDER}
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
            />
          </div>

          {status.message && (
            <div
              className={`flex items-center gap-2 text-sm p-3 rounded-md ${
                status.type === "success"
                  ? "bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                  : "bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400"
              }`}
            >
              {status.type === "success" ? (
                <CheckCircle2 className="h-4 w-4 shrink-0" />
              ) : (
                <AlertCircle className="h-4 w-4 shrink-0" />
              )}
              <span>{status.message}</span>
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex flex-col items-start gap-4 border-t pt-6">
        <Button className="w-full" onClick={handleConnect} disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {GITHUB_CONFIG.TEXT.BUTTON_CONNECTING}
            </>
          ) : (
            GITHUB_CONFIG.TEXT.BUTTON_CONNECT
          )}
        </Button>
        <p className="text-xs text-muted-foreground">
          {GITHUB_CONFIG.TEXT.FOOTER_NOTE}
        </p>
      </CardFooter>
    </Card>
  );
}
