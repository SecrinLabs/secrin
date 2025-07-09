import { useMutation } from "@tanstack/react-query";

const toggleIntegration = async (integrationName: string) => {
  const response = await fetch(
    `http://localhost:8000/api/integration/toggle?name=${integrationName}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error("Failed to Enable Integration");
  }

  return response.json();
};

export const useEnableEmbedder = () => {
  return useMutation({
    mutationFn: (integrationType: string) => toggleIntegration(integrationType),
    onSuccess: (_, integrationType) => {
      console.log("Integration enabled for:", integrationType);
    },
    onError: (error: any) => {
      console.error("Integration failed to toggle for:", error);
    },
  });
};
