export interface SaveInstallationTokenRequest {
  installation_token: string;
  user_guid: string;
}

export interface SaveRepositoryList {
  user_guid: string;
  repository_list: {
    id: number; // GitHub repo id
    name: string; // repo_name
    full_name: string; // owner/repo
    url: string; // api url or html_url
    html_url: string;
    description: string | null;
    private: boolean;
    language: string | null;
    topics: string[];
    stargazers_count: number;
    forks_count: number;
    watchers_count: number;
    default_branch: string;
    open_issues_count: number;
    has_issues: boolean;
    has_discussions: boolean;
    archived: boolean;
    created_at: string; // ISO8601 timestamp
    updated_at: string; // ISO8601 timestamp
    pushed_at: string; // ISO8601 timestamp
    clone_url: string;
    owner: {
      login: string;
      type: string;
    };
  }[];
}

export interface DisconnectServiceRequest {
  user_guid: string;
  service_type: string;
}

export interface GetAllIntegrationsRequest {
  user_guid: string;
}

export interface IntegrationDTO {
  id: string;
  type: string;
}

export interface GetUserIntegrationsResponse {
  integrations: IntegrationDTO[];
}

export interface SaveDiscordTokenRequestDTO {
  code: string;
  guild_id: string;
}
