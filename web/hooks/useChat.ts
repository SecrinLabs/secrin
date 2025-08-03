import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  sendChatMessage,
  ChatRequest,
  ChatResponse,
  ChatApiError,
} from "@/service/chat";

export interface UseChatMutationOptions {
  onSuccess?: (data: ChatResponse, variables: ChatRequest) => void;
  onError?: (error: ChatApiError, variables: ChatRequest) => void;
}

export function useChat(options?: UseChatMutationOptions) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: (data, variables) => {
      // Optionally cache successful chat responses
      queryClient.setQueryData(["chat", variables.conversation_id], data);
      options?.onSuccess?.(data, variables);
    },
    onError: (error: ChatApiError, variables) => {
      console.error("Chat API Error:", error);
      options?.onError?.(error, variables);
    },
  });

  return {
    sendMessage: mutation.mutate,
    sendMessageAsync: mutation.mutateAsync,
    isLoading: mutation.isPending,
    error: mutation.error,
    data: mutation.data,
    isError: mutation.isError,
    isSuccess: mutation.isSuccess,
    reset: mutation.reset,
  };
}

export type UseChatReturn = ReturnType<typeof useChat>;
