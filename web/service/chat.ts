import env from "@/config/env";
import { getFriendlyErrorMessage } from "@/lib/HttpError";
import { ChatApiError, ChatRequest, ChatResponse } from "@/types";
import { getSession } from "next-auth/react";

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  try {
    const session = await getSession();
    if (!session?.accessToken) {
      throw new ChatApiError("User is not authenticated", 401);
    }
    const response = await fetch(`${env.api.url}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.accessToken}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const friendlyMessage = getFriendlyErrorMessage(
        response.status,
        errorData.message || response.statusText
      );

      throw new ChatApiError(friendlyMessage, response.status, errorData);
    }

    const data = await response.json();

    const answer = data?.data?.answer;
    // Validate response structure
    if (!answer) {
      throw new ChatApiError("Invalid response format from server", 500, data);
    }

    return {
      answer: answer,
      timestamp: data.timestamp || new Date().toISOString(),
    };
  } catch (error) {
    if (error instanceof ChatApiError) {
      throw error;
    }

    // Handle network errors and other unexpected errors
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new ChatApiError("Unable to connect to chat service", 0);
    }

    throw new ChatApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}
