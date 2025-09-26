import env from "@/config/env";

import {
  AddGithubRepositoryRequest,
  CommonAPIResponse,
  GetAllSourcesRequest,
  GetAllSourcesResponse,
  GetGithubRemainingRepositoryRequest,
  GetGithubRemainingRepositoryResponse,
  RemoveGithubRepositoryRequest,
  SourceApiError,
} from "@/types";
import { getSession } from "next-auth/react";

export async function getUserSources(
  request: GetAllSourcesRequest
): Promise<CommonAPIResponse<GetAllSourcesResponse>> {
  try {
    const session = await getSession();
    if (!session?.accessToken) {
      throw new SourceApiError("User is not authenticated", 401);
    }
    const response = await fetch(
      `${env.api.url}/api/source/get-all-integrations`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new SourceApiError(
        errorData.message || response.statusText,
        response.status,
        errorData
      );
    }

    const data: CommonAPIResponse = await response.json();

    if (typeof data.success !== "boolean" || !data.message) {
      throw new SourceApiError(
        "Invalid response format from server",
        500,
        data
      );
    }

    return data as CommonAPIResponse<GetAllSourcesResponse>;
  } catch (error) {
    if (error instanceof SourceApiError) throw error;

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new SourceApiError("Unable to connect to backend service", 0);
    }

    throw new SourceApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}

export async function getGithubRemainingRepository(
  request: GetGithubRemainingRepositoryRequest
): Promise<CommonAPIResponse<GetGithubRemainingRepositoryResponse>> {
  try {
    const session = await getSession();
    if (!session?.accessToken) {
      throw new SourceApiError("User is not authenticated", 401);
    }
    const response = await fetch(
      `${env.api.url}/api/source/github/get-remaining-repository`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new SourceApiError(
        errorData.message || response.statusText,
        response.status,
        errorData
      );
    }

    const data: CommonAPIResponse = await response.json();

    if (typeof data.success !== "boolean" || !data.message) {
      throw new SourceApiError(
        "Invalid response format from server",
        500,
        data
      );
    }

    return data as CommonAPIResponse<GetGithubRemainingRepositoryResponse>;
  } catch (error) {
    if (error instanceof SourceApiError) throw error;

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new SourceApiError("Unable to connect to backend service", 0);
    }

    throw new SourceApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}

export async function deleteGithubRepository(
  request: RemoveGithubRepositoryRequest
): Promise<CommonAPIResponse> {
  try {
    const session = await getSession();
    if (!session?.accessToken) {
      throw new SourceApiError("User is not authenticated", 401);
    }
    const response = await fetch(
      `${env.api.url}/api/source/github/remove-repository`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new SourceApiError(
        errorData.message || response.statusText,
        response.status,
        errorData
      );
    }

    const data: CommonAPIResponse = await response.json();

    if (typeof data.success !== "boolean" || !data.message) {
      throw new SourceApiError(
        "Invalid response format from server",
        500,
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof SourceApiError) throw error;

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new SourceApiError("Unable to connect to backend service", 0);
    }

    throw new SourceApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}

export async function addGithubRepository(
  request: AddGithubRepositoryRequest
): Promise<CommonAPIResponse> {
  try {
    const session = await getSession();
    if (!session?.accessToken) {
      throw new SourceApiError("User is not authenticated", 401);
    }
    const response = await fetch(
      `${env.api.url}/api/source/github/add-repository`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new SourceApiError(
        errorData.message || response.statusText,
        response.status,
        errorData
      );
    }

    const data: CommonAPIResponse = await response.json();

    if (typeof data.success !== "boolean" || !data.message) {
      throw new SourceApiError(
        "Invalid response format from server",
        500,
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof SourceApiError) throw error;

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new SourceApiError("Unable to connect to backend service", 0);
    }

    throw new SourceApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}
