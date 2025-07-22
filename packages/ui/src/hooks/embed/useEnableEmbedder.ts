import { useMutation } from "@tanstack/react-query";

import { endpoints } from "@workspace/ui/lib/config";

const enableEmbedder = async (integrationName: string) => {
  const response = await fetch(endpoints.integrationToggle(integrationName), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to Enable Integration");
  }

  return response.json();
};

export const useEnableEmbedder = () => {
  return useMutation({
    mutationFn: (integrationType: string) => enableEmbedder(integrationType),
    onSuccess: (_, integrationType) => {
      console.log("Integration enabled for:", integrationType);
    },
    onError: (error: any) => {
      console.error("Integration failed to toggle for:", error);
    },
  });
};
