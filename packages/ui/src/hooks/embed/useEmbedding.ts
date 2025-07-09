import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

const startEmbedding = async () => {
  const response = await fetch(
    `http://localhost:8000/api/embed/start-embeding`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

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
