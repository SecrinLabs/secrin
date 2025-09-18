import env from "@/config/env";

import {
  CommonAPIResponse,
  GetAllSourcesRequest,
  GetAllSourcesResponse,
  SourceApiError,
} from "@/types";

export async function getUserIntegrations(
  request: GetAllSourcesRequest
): Promise<CommonAPIResponse<GetAllSourcesResponse>> {
  try {
    const response = await fetch(
      `${env.api.url}/api/source/get-all-integrations`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
