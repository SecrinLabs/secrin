import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

const startScraping = async (integrationType: string) => {
  const response = await fetch(
    `http://localhost:8000/api/scraper/start-scraper/${integrationType}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ type: integrationType }),
    },
  );

  if (!response.ok) {
    throw new Error("Failed to start Scraper");
  }

  return response.json(); // or return some confirmation if needed
};

export const useStartScraper = () => {
  return useMutation({
    mutationFn: (integrationType: string) => startScraping(integrationType),
    onSuccess: (_, integrationType) => {
      toast.success(`Scraper started for ${integrationType}`);
      console.log("Scraper started for:", integrationType);
    },
    onError: (error: any) => {
      toast.error("Failed to start Scraper");
      console.error("Error starting Scraper:", error);
    },
  });
};
