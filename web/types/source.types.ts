export interface GetAllSourcesRequest {
  user_id: string;
}

// Metadata types for each source
export interface RepositoryMetadata {
  url: string;
  created_at?: string;
}

// Integration types (discriminated union)
export type Integration = {
  id: number;
  type: "repository";
  name: string;
  metadata: RepositoryMetadata;
};

// 3. Response wrapper
export interface GetAllSourcesResponse {
  success: boolean;
  message: string;
  data: {
    integrations: Integration[];
  };
}
