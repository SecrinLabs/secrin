"use client";

import React, { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Github, BookOpen, Loader2, FilePlus, Clock } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Integration, RemoveGithubRepositoryRequest } from "@/types";
import { deleteGithubRepository, getUserSources } from "@/service/source";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Icons } from "@/components/Icons";
import { redirect } from "next/navigation";
import { toast } from "sonner";

// Utility: choose icon based on type
const getIconForType = (type: Integration["type"]) => {
  switch (type) {
    case "repository":
      return Github;
    default:
      return BookOpen; // fallback
  }
};

function Page() {
  const [sourceList, setSourceList] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingButtons, setLoadingButtons] = useState<Record<number, boolean>>(
    {}
  );
  const { data: session, status } = useSession();

  useEffect(() => {
    const fetchSources = async () => {
      setLoading(true);
      try {
        if (status === "loading") return;
        if (!session?.user?.id) return;

        const response = await getUserSources({
          user_id: session.user.id.toString(),
        });

        // Assuming your API returns: { success, message, data: { integrations: [] } }
        setSourceList(response.data?.integrations ?? []);
      } catch {
        toast.error("some error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchSources();
  }, [status, session?.user?.id]);

  const handleClick = async (id: number) => {
    setLoadingButtons((prev) => ({ ...prev, [id]: true }));
    try {
      const request: RemoveGithubRepositoryRequest = {
        user_id: session?.user?.id ?? "", // wherever you keep the logged-in user id
        repo_id: id,
      };

      const response = await deleteGithubRepository(request);

      if (response.success) {
        setSourceList(sourceList.filter((repo) => repo.metadata.repo_id != id));
        toast.success("Repository Removed Successfully");
      } else {
        alert(`Failed to remove repository: ${response.message}`);
      }
    } catch {
      toast.error("some error occurred");
      alert("Something went wrong while removing the repository");
    } finally {
      setLoadingButtons((prev) => ({ ...prev, [id]: false }));
    }
  };

  if (status === "loading" || loading) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[200px]">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Loading...</span>
      </div>
    ); // ✅ central loading UI
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6 max-w-5xl mx-auto">
      <div className="space-y-4">
        <div className="flex justify-between">
          <h1 className="text-3xl font-bold tracking-tight">
            Knowledge Source
          </h1>
          <div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button size="sm">
                  <FilePlus /> New Source
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                side="bottom"
                align="end"
                sideOffset={4}
              >
                <DropdownMenuGroup>
                  <DropdownMenuItem onClick={() => redirect("/source/github")}>
                    <Icons.github />
                    GitHub Repository
                  </DropdownMenuItem>
                  <DropdownMenuItem disabled>
                    <Clock />
                    Jira (Soon)
                  </DropdownMenuItem>
                  <DropdownMenuItem disabled>
                    <Clock />
                    Documentation (Soon)
                  </DropdownMenuItem>
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        <p className="text-muted-foreground text-lg">
          Connect your repositories to access and manage your sources in one
          place.
        </p>
      </div>

      <div className="space-y-4">
        {sourceList.length === 0 ? (
          <div className="flex items-center justify-between rounded-xl border bg-card shadow-sm p-5">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-muted p-3">
                <BookOpen className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <div className="font-semibold text-lg">
                  No knowledge sources found
                </div>
                <p className="text-sm text-muted-foreground">
                  Add a source to get started.
                </p>
              </div>
            </div>
          </div>
        ) : (
          sourceList.map((source) => {
            const Icon = getIconForType(source.type);
            const isLoading = loadingButtons[source.metadata.repo_id] ?? false;

            return (
              <div
                key={source.id}
                className="flex items-center justify-between rounded-xl border bg-card shadow-sm p-5 hover:shadow-md transition"
              >
                <div className="flex items-start gap-4">
                  <div className="rounded-lg bg-muted p-3">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <div className="font-semibold text-lg">{source.name}</div>
                    <p className="text-sm text-muted-foreground">
                      {source.type} source
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant={isLoading ? "outline" : "outline"}
                  disabled={isLoading}
                  onClick={() => handleClick(source.metadata.repo_id)}
                >
                  {isLoading ? "Removing..." : "Remove"}
                </Button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default Page;
