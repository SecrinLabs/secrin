"use client";

import {
  addGithubRepository,
  getGithubRemainingRepository,
} from "@/service/source";
import { RepositoryMetadata } from "@/types";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { BookOpen, Github, Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function Page() {
  const [repos, setRepos] = useState<RepositoryMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingRepoId, setLoadingRepoId] = useState<number | null>(null);
  const { data: session, status } = useSession();

  useEffect(() => {
    const fetchRepos = async () => {
      setLoading(true);
      try {
        if (status === "loading") return;
        if (!session?.user?.userGUID) return;

        const response = await getGithubRemainingRepository({
          user_guid: session.user.userGUID,
        });

        setRepos(response.data?.repositorys || []);
      } catch {
        toast.error("some error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchRepos();
  }, [status, session?.user?.userGUID]);

  async function handleClick(repoId: number) {
    try {
      if (status === "loading") return;
      if (!session?.user?.userGUID) return;

      setLoadingRepoId(repoId);

      const response = await addGithubRepository({
        user_guid: session.user.userGUID,
        repo_id: repoId,
      });

      if (response.success) {
        toast.success("Repository Added Successfully");
      }

      // remove repo from local list after adding
      setRepos((prev) => prev.filter((repo) => repo.repo_id !== repoId));
    } catch {
      toast.error("some error occurred");
    } finally {
      setLoadingRepoId(null);
    }
  }

  if (status === "loading" || loading) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[200px]">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Loading...</span>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold tracking-tight">GitHub Repositories</h1>
      <p className="text-muted-foreground text-lg">
        Connect your GitHub repositories to enable query-based answers directly
        from your codebase.
      </p>
      <div className="space-y-4">
        {repos.length == 0 ? (
          <div className="flex items-center justify-between rounded-xl border bg-card shadow-sm p-5">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-muted p-3">
                <BookOpen className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <div className="font-semibold text-lg">
                  No repositories available 🎉
                </div>
                <p className="text-sm text-muted-foreground">
                  No more repositories left to add.
                </p>
              </div>
            </div>
          </div>
        ) : (
          repos.map((repo) => (
            <div
              key={repo.repo_id}
              className="flex items-center justify-between rounded-xl border bg-card shadow-sm p-5 hover:shadow-md transition"
            >
              <div className="flex items-start gap-4">
                <div className="rounded-lg bg-muted p-3">
                  <Github className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <div className="font-semibold text-lg">{repo.name}</div>
                  <a
                    href={repo.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-muted-foreground hover:underline"
                  >
                    {repo.url}
                  </a>
                </div>
              </div>
              <Button
                size="sm"
                variant="outline"
                disabled={loadingRepoId === repo.repo_id}
                onClick={() => handleClick(repo.repo_id)}
              >
                {loadingRepoId === repo.repo_id ? "Adding..." : "Add"}
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
