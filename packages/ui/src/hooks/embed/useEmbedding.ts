import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { endpoints } from "@workspace/ui/lib/config";

const startEmbedding = async () => {
  const response = await fetch(endpoints.embed, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to start Embedding");
  }

  return response.json();
};

export const useStartEmbedding = () => {
  return useMutation({
    mutationFn: () => startEmbedding(),
    onSuccess: (_) => {
      toast.success(`Embedding started`);
    },
    onError: (error: any) => {
      toast.error("Failed to start Embedding");
    },
  });
};
