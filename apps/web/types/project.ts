export interface Project {
  id: string;
  name: string;
  description?: string;
  repoName: string;
  repoUrl?: string;
  createdAt: string;
  status: ProjectStatus;
}

export type ProjectStatus = "pending" | "creating" | "active" | "error";

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
