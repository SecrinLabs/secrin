export interface Project {
  id: string;
  name: string;
  slug?: string;
  description?: string;
  repoName: string;
  repoUrl?: string;
  githubOwner?: string;
  createdAt: string;
  status: ProjectStatus;
  // Source repository fields
  sourceRepoUrl?: string;
  sourceRepoOwner?: string;
  sourceRepoName?: string;
  sourceRepoBranch?: string;
  lastDocGenAt?: string;
  docGenStatus?: DocGenStatus;
}

export type ProjectStatus = "pending" | "creating" | "active" | "error";

export type DocGenStatus = "pending" | "running" | "success" | "failed";

export interface CreateProjectRequest {
  name: string;
  description?: string;
  repoName: string;
}

export interface CreateProjectResponse {
  success: boolean;
  message: string;
  data: {
    project: Project;
    repoUrl: string;
  };
}

export interface GitHubAppInstallationStatus {
  installed: boolean;
  installationId?: number;
  accountLogin?: string;
}

export interface GitHubAppInstallationResponse {
  success: boolean;
  message: string;
  data: GitHubAppInstallationStatus;
}

export type ProjectWizardStep = "github-app" | "project-details" | "creating";
