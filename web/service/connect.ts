import env from "@/config/env";
import { getFriendlyErrorMessage } from "@/lib/HttpError";

// types.ts
export interface SaveInstallationTokenRequest {
  installation_token: string; // note: looks like an int in example, but keep string to support GitHub’s actual token format
  user_id: number;
}

export interface SaveInstallationTokenResponse {
  success: boolean;
  message: string;
  data?: unknown;
}

// errors.ts (reusing your ChatApiError)
export class GithubApiError extends Error {
  constructor(message: string, public status: number, public data?: unknown) {
    super(message);
    this.name = "GithubApiError";
  }
}

export async function saveInstallationToken(
  request: SaveInstallationTokenRequest
): Promise<SaveInstallationTokenResponse> {
  try {
    const response = await fetch(
      `${env.api.url}/api/connect/github/save-installation-token`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const friendlyMessage = getFriendlyErrorMessage(
        response.status,
        errorData.message || response.statusText
      );
      throw new GithubApiError(friendlyMessage, response.status, errorData);
    }

    const data: SaveInstallationTokenResponse = await response.json();

    if (typeof data.success !== "boolean" || !data.message) {
      throw new GithubApiError(
        "Invalid response format from server",
        500,
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof GithubApiError) {
      throw error;
    }

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new GithubApiError("Unable to connect to GitHub service", 0);
    }

    throw new GithubApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}

export interface SaveRepositoryList {
  user_id: number;
  repository_list: {
    name: string;
    url: string;
  }[];
}

export async function saveRepositoryList(
  request: SaveRepositoryList
): Promise<SaveInstallationTokenResponse> {
  try {
    const response = await fetch(
      `${env.api.url}/api/connect/github/save-repository`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const friendlyMessage = getFriendlyErrorMessage(
        response.status,
        errorData.message || response.statusText
      );
      throw new GithubApiError(friendlyMessage, response.status, errorData);
    }

    const data: SaveInstallationTokenResponse = await response.json();

    if (typeof data.success !== "boolean" || !data.message) {
      throw new GithubApiError(
        "Invalid response format from server",
        500,
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof GithubApiError) {
      throw error;
    }

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new GithubApiError("Unable to connect to GitHub service", 0);
    }

    throw new GithubApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}
