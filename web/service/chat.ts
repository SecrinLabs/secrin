export interface ChatRequest {
  question: string;
  conversation_id?: string;
}

export interface ChatResponse {
  answer: string;
  conversation_id?: string;
  timestamp?: string;
}

export interface ApiError {
  message: string;
  status: number;
}

export class ChatApiError extends Error {
  constructor(message: string, public status: number, public data?: unknown) {
    super(message);
    this.name = "ChatApiError";
  }
}

import env from "@/config/env";

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
      throw new ChatApiError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
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
