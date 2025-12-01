export interface GitHubConnectRequest {
  repo_url: string;
}

export interface GitHubConnectResponseData {
  connection_id: string;
  provider: string;
  repo_url: string;
  owner: string;
  repository: string;
  full_name: string;
  status: string;
  has_token: boolean;
}

export interface GitHubConnectResponse {
  success: boolean;
  message: string;
  data: GitHubConnectResponseData;
  status_code: number;
}
