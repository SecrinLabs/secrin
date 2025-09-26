export interface GetAllSourcesRequest {
  user_guid: string;
}

export interface RepositoryMetadata {
  url: string;
  created_at?: string;
  repo_id: number;
  name: string;
}

export type Integration = {
  id: number;
  type: "repository";
  name: string;
  metadata: RepositoryMetadata;
};

export interface GetAllSourcesResponse {
  integrations: Integration[];
}

export interface GetGithubRemainingRepositoryRequest {
  user_guid: string;
}

export interface GetGithubRemainingRepositoryResponse {
  repositorys: RepositoryMetadata[];
}

export interface RemoveGithubRepositoryRequest {
  user_guid: string;
  repo_id: number;
}

export interface AddGithubRepositoryRequest {
  user_guid: string;
  repo_id: number;
}
