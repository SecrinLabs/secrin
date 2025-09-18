export interface GetAllSourcesRequest {
  user_id: string;
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
  user_id: string;
}

export interface GetGithubRemainingRepositoryResponse {
  repositorys: RepositoryMetadata[];
}

export interface RemoveGithubRepositoryRequest {
  user_id: string;
  repo_id: number;
}

export interface AddGithubRepositoryRequest {
  user_id: string;
  repo_id: number;
}
