import { ApiClient } from "@/lib/api-client";
import { PROJECT_CONFIG } from "@/constants/project";
import {
  CreateProjectRequest,
  CreateProjectResponse,
  GitHubAppInstallationResponse,
} from "@/types/project";

export const ProjectService = {
  checkGitHubAppInstallation: async (): Promise<GitHubAppInstallationResponse> => {
    return ApiClient.get<GitHubAppInstallationResponse>(
      PROJECT_CONFIG.API_ENDPOINTS.GITHUB_INSTALLATION_STATUS
    );
  },

  createProject: async (
    data: CreateProjectRequest
  ): Promise<CreateProjectResponse> => {
    return ApiClient.post<CreateProjectResponse>(
      PROJECT_CONFIG.API_ENDPOINTS.CREATE_PROJECT,
      data
    );
  },
};
