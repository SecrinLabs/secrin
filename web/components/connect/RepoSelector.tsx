"use client";

import * as React from "react";
import { ChevronsUpDown, GitFork, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

export type Repository = {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  private: boolean;
  fork: boolean;
  stargazers_count: number;
};

interface RepoSelectorProps {
  repositories: Repository[];
  onSelect: (repos: Repository[]) => void;
  selectedIds?: number[];
}

export function RepoSelector({
  repositories,
  onSelect,
  selectedIds = [],
}: RepoSelectorProps) {
  const [open, setOpen] = React.useState(false);

  const selectedRepos = React.useMemo(
    () => repositories.filter((repo) => selectedIds.includes(repo.id)),
    [repositories, selectedIds]
  );

  const handleSelect = (repo: Repository) => {
    const isSelected = selectedIds.includes(repo.id);
    const newSelectedRepos = isSelected
      ? selectedRepos.filter((r) => r.id !== repo.id)
      : [...selectedRepos, repo];
    onSelect(newSelectedRepos);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          {selectedRepos.length > 0
            ? `${selectedRepos.length} repositories selected`
            : "Select repositories..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0">
        <Command>
          <CommandInput placeholder="Search repositories..." />
          <CommandEmpty>No repositories found.</CommandEmpty>
          <CommandGroup className="max-h-[300px] overflow-auto">
            {repositories.map((repo) => (
              <CommandItem
                key={repo.id}
                onSelect={() => handleSelect(repo)}
                className="flex flex-col items-start gap-1 py-3"
              >
                <div className="flex w-full items-center gap-2">
                  <Checkbox
                    checked={selectedIds.includes(repo.id)}
                    className="mr-2"
                    onCheckedChange={() => handleSelect(repo)}
                  />
                  <span className="font-medium">{repo.full_name}</span>
                  <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
                    {repo.fork && (
                      <span className="flex items-center gap-1">
                        <GitFork className="h-3 w-3" />
                        Fork
                      </span>
                    )}
                    {repo.stargazers_count > 0 && (
                      <span className="flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        {repo.stargazers_count}
                      </span>
                    )}
                  </div>
                </div>
                {repo.description && (
                  <span className="text-xs text-muted-foreground line-clamp-2 pl-8">
                    {repo.description}
                  </span>
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
