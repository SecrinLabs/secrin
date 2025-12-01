import { ApiClient } from "@/lib/api-client";
import { GITHUB_CONFIG } from "@/constants/integrations/github";
import {
  GitHubConnectRequest,
  GitHubConnectResponse,
} from "@/types/integrations/github";

export const GitHubService = {
  connectRepository: async (
    repoUrl: string
  ): Promise<GitHubConnectResponse> => {
    const payload: GitHubConnectRequest = { repo_url: repoUrl };
    return ApiClient.post<GitHubConnectResponse>(
      GITHUB_CONFIG.API_ENDPOINTS.CONNECT,
      payload
    );
  },
};
