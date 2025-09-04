import env from "@/config/env";
import { getFriendlyErrorMessage } from "@/lib/HttpError";
import {
  CommonAPIResponse,
  GithubApiError,
  SaveInstallationTokenRequest,
  SaveRepositoryList,
} from "@/types";

export async function saveInstallationToken(
  request: SaveInstallationTokenRequest
): Promise<CommonAPIResponse> {
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

    const data: CommonAPIResponse = await response.json();

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

export async function saveRepositoryList(
  request: SaveRepositoryList
): Promise<CommonAPIResponse> {
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

    const data: CommonAPIResponse = await response.json();

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
