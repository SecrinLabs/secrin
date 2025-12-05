import { ENV } from "@/config/env";
import type { AgentType, ChatRequest, StreamChunk } from "@/types/chat";

/**
 * Chat service for handling streaming chat requests
 */
export const ChatService = {
  /**
   * Send a chat request with streaming support
   * Returns an async generator that yields parsed stream chunks
   */
  streamChat: async function* (
    question: string,
    agentType: AgentType,
    options?: {
      searchType?: "vector" | "hybrid";
      contextLimit?: number;
    }
  ): AsyncGenerator<StreamChunk> {
    const request: ChatRequest = {
      question,
      agent_type: agentType,
      search_type: options?.searchType ?? "hybrid",
      context_limit: options?.contextLimit ?? 5,
      stream: true,
    };

    const response = await fetch(`${ENV.API_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE events
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();

            if (data === "[DONE]") {
              return;
            }

            try {
              const rawChunk = JSON.parse(data);

              // Transform backend format to frontend format
              if (rawChunk.context) {
                // Context message
                yield {
                  type: "context",
                  context: rawChunk.context,
                  metadata: {
                    model: rawChunk.model,
                    provider: rawChunk.provider,
                    node_types: rawChunk.node_types,
                  },
                };
              } else if (rawChunk.chunk) {
                // Answer chunk
                yield {
                  type: "answer_chunk",
                  content: rawChunk.chunk,
                };
              } else if (rawChunk.done) {
                // Done signal
                return;
              } else if (rawChunk.error) {
                yield {
                  type: "error",
                  error: rawChunk.error,
                };
              }
            } catch {
              // Skip malformed JSON
              console.warn("Failed to parse SSE chunk:", data);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  /**
   * Send a non-streaming chat request
   */
  chat: async (
    question: string,
    agentType: AgentType,
    options?: {
      searchType?: "vector" | "hybrid";
      contextLimit?: number;
    }
  ) => {
    const request: ChatRequest = {
      question,
      agent_type: agentType,
      search_type: options?.searchType ?? "hybrid",
      context_limit: options?.contextLimit ?? 5,
      stream: false,
    };

    const response = await fetch(`${ENV.API_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },
};
