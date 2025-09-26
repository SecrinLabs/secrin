"use client";

import { saveInstallationToken, saveRepositoryList } from "@/service/connect";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Github, CheckCircle2, XCircle, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Repository } from "./RepoSelector";

export default function GithubSuccess({
  installation_token,
  userId,
}: {
  installation_token?: string | null;
  userId?: string | null;
}) {
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");

  const saveToken = useCallback(async () => {
    try {
      if (!installation_token) throw new Error("Invalid token");
      if (!userId) throw new Error("User not authenticated");

      setStatus("loading");

      const res = await saveInstallationToken({
        installation_token,
        user_guid: userId,
      });

      if (!res.success) throw new Error(res.message || "Failed to save token");

      const data = res.data as { repos?: Repository[] };

      console.log(data.repos);

      getAndSaveRepository(data.repos || []);

      setStatus("success");
      setMessage(res.message || "Token saved successfully");
    } catch (err: unknown) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Unexpected error");
    }
  }, [installation_token, userId]);

  async function getAndSaveRepository(repositories: Repository[]) {
    // Map into payload structure
    const payload = repositories.map((repo) => ({
      id: repo.id,
      name: repo.name,
      full_name: repo.full_name,
      url: repo.url ?? `https://api.github.com/repos/${repo.full_name}`, // fallback
      html_url: repo.html_url,
      description: repo.description,
      private: repo.private,
      language: repo.language,
      topics: repo.topics ?? [],
      stargazers_count: repo.stargazers_count,
      forks_count: repo.forks_count,
      watchers_count: repo.watchers_count,
      default_branch: repo.default_branch,
      open_issues_count: repo.open_issues_count,
      has_issues: repo.has_issues,
      has_discussions: repo.has_discussions,
      archived: repo.archived,
      created_at: repo.created_at,
      updated_at: repo.updated_at,
      pushed_at: repo.pushed_at,
      clone_url: repo.clone_url,
      owner: {
        login: repo.owner?.login,
        type: repo.owner?.type,
      },
    }));

    const res = await saveRepositoryList({
      repository_list: payload,
      user_guid: userId || "",
    });
  }

  useEffect(() => {
    if (installation_token && userId) {
      void saveToken();
    }
  }, [installation_token, userId, saveToken]);

  if (!userId) {
    return (
      <main className="min-h-screen bg-muted flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto h-12 w-12 rounded-full bg-background shadow-sm ring-1 ring-border flex items-center justify-center">
              <Github aria-hidden="true" className="h-6 w-6 text-foreground" />
              <span className="sr-only">GitHub</span>
            </div>
            <CardTitle className="text-balance">Sign in required</CardTitle>
            <CardDescription className="text-pretty">
              Please sign in to save your GitHub installation token to your
              account.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertTitle>Authentication needed</AlertTitle>
              <AlertDescription>
                We couldn&apos;t detect an active session. After you sign in,
                return to this page and try again.
              </AlertDescription>
            </Alert>
            <div className="flex items-center justify-center gap-3">
              <Button asChild>
                <Link href="/api/auth/signin" aria-label="Sign in">
                  Sign in
                </Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/">Go home</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    );
  }

  if (status === "loading" || status === "idle") {
    return (
      <main className="min-h-screen bg-muted flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto h-12 w-12 rounded-full bg-background shadow-sm ring-1 ring-border flex items-center justify-center">
              <Github aria-hidden="true" className="h-6 w-6 text-foreground" />
              <span className="sr-only">GitHub</span>
            </div>
            <CardTitle className="text-balance">Connecting GitHub…</CardTitle>
            <CardDescription className="text-pretty">
              Saving your GitHub installation token to your account.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div
              className="flex items-center gap-3"
              role="status"
              aria-live="polite"
            >
              <LoaderCircle className="h-5 w-5 animate-spin text-foreground/70" />
              <span className="text-sm text-muted-foreground">
                Working on it…
              </span>
            </div>
            <Progress className="h-2" value={undefined} />
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Verifying your session</li>
              <li>• Linking installation to your profile</li>
              <li>• Finalizing connection</li>
            </ul>
            <p className="text-xs text-muted-foreground">
              You can safely close this tab; we’ll finish in the background.
            </p>
          </CardContent>
        </Card>
      </main>
    );
  }

  if (status === "error") {
    return (
      <main className="min-h-screen bg-muted flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto h-12 w-12 rounded-full bg-background shadow-sm ring-1 ring-border flex items-center justify-center">
              <XCircle aria-hidden="true" className="h-6 w-6 text-red-600" />
              <span className="sr-only">Error</span>
            </div>
            <CardTitle className="text-balance">We hit a snag</CardTitle>
            <CardDescription className="text-pretty">
              We couldn’t save your installation token. Try again below.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive" role="alert" aria-live="assertive">
              <AlertTitle>Token save failed</AlertTitle>
              <AlertDescription>
                {message || "An unexpected error occurred."}
              </AlertDescription>
            </Alert>

            <div className="flex items-center justify-between gap-3">
              <Button
                variant="default"
                onClick={saveToken}
                className="min-w-24"
                aria-label="Retry saving token"
              >
                Retry
              </Button>
              <div className="flex items-center gap-2">
                <Button variant="outline" asChild>
                  <Link href="/">Go home</Link>
                </Button>
                <Button variant="ghost" asChild>
                  <a
                    href="mailto:support@example.com?subject=GitHub%20Installation%20Help"
                    aria-label="Contact support"
                  >
                    Contact support
                  </a>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-muted flex items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto h-12 w-12 rounded-full bg-background shadow-sm ring-1 ring-border flex items-center justify-center">
            <CheckCircle2
              aria-hidden="true"
              className="h-7 w-7 text-green-600"
            />
            <span className="sr-only">Success</span>
          </div>
          <CardTitle className="text-balance">You’re all set!</CardTitle>
          <CardDescription className="text-pretty">
            {message || "Token saved successfully."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md p-3 bg-background ring-1 ring-border">
            <div className="flex items-center gap-2 text-sm">
              <Github
                className="h-4 w-4 text-foreground/80"
                aria-hidden="true"
              />
              <span className="text-muted-foreground">
                Your GitHub app is now linked to your account.
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
