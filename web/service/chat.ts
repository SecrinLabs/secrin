import env from "@/config/env";
import { getFriendlyErrorMessage } from "@/lib/HttpError";
import { ChatApiError, ChatRequest, ChatResponse } from "@/types";

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  try {
    console.log(JSON.stringify(request));
    const response = await fetch(`${env.api.url}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
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

    // Validate response structure
    if (!data.answer) {
      throw new ChatApiError("Invalid response format from server", 500, data);
    }

    return {
      answer: data.answer,
      conversation_id: data.conversation_id || "",
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
