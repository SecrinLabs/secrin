import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

const startEmbedding = async (integrationType: string) => {
  const response = await fetch(
    `http://localhost:8000/api/scraper/start-scraper/${integrationType}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ type: integrationType }),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to start embedding");
  }

  return response.json(); // or return some confirmation if needed
};

export const useStartEmbedding = () => {
  return useMutation({
    mutationFn: (integrationType: string) => startEmbedding(integrationType),
    onSuccess: (_, integrationType) => {
      toast.success(`Embedding started for ${integrationType}`);
      console.log("Embedding started for:", integrationType);
    },
    onError: (error: any) => {
      toast.error("Failed to start embedding");
      console.error("Error starting embedding:", error);
    },
  });
};
