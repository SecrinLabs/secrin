import { useMutation } from "@tanstack/react-query";
import { Integration } from "@workspace/ui/types/Integration";

const fetchIntegrations = async (): Promise<Integration[]> => {
  const response = await fetch(`http://localhost:8000/api/integration`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch integrations");
  }

  const data: Integration[] = await response.json();
  return data;
};

export const useLoadIntegration = () => {
  return useMutation<Integration[]>({
    mutationFn: fetchIntegrations,
    onSuccess: (data) => {
      console.log("Integrations loaded", data);
    },
    onError: (err) => {
      console.error("Failed to load integrations", err);
    },
  });
};
