import { Github, BookOpen, FolderOpen } from "lucide-react";

export type IntegrationName = "github" | "sitemap" | "gitlocal";

export type GithubConfig = {
  username?: string;
  token?: string;
  repoUrl?: string;
};
export type SitemapConfig = {
  docType: string;
  sitemapUrl: string;
};
export type GitLocalConfig = {
  repo_path?: string;
  localPath?: string;
  projectName?: string;
};

export type IntegrationConfig =
  | {
      name: "github";
      config: GithubConfig;
    }
  | {
      name: "sitemap";
      config: SitemapConfig;
    }
  | {
      name: "gitlocal";
      config: GitLocalConfig;
    };

export const IntegrationUIMap: Record<
  IntegrationName,
  {
    icon: typeof Github;
    description: string;
    color: string;
  }
> = {
  github: {
    icon: Github,
    description:
      "Connect your GitHub repositories to sync code and documentation",
    color: "bg-gradient-to-br from-gray-900 to-gray-700",
  },
  sitemap: {
    icon: BookOpen,
    description: "Configure and manage your project documentation settings",
    color: "bg-gradient-to-br from-blue-600 to-blue-800",
  },
  gitlocal: {
    icon: FolderOpen,
    description: "Add local repositories from your development environment",
    color: "bg-gradient-to-br from-emerald-600 to-emerald-800",
  },
};

export type Integration = {
  id: string;
  name: IntegrationName;
  is_connected: boolean;
} & IntegrationConfig;
