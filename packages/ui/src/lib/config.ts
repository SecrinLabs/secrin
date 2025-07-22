// Configuration for UI package
// This will use environment variables if available, with fallback to localhost
const getApiBaseUrl = () => {
  // Check for various environment variable names that might be used
  if (typeof window !== "undefined") {
    // Client-side
    return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  } else {
    // Server-side
    return (
      process.env.API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      "http://localhost:8000"
    );
  }
};

export const config = {
  apiBaseUrl: getApiBaseUrl(),
} as const;

// API endpoints for UI package
export const endpoints = {
  embed: `${config.apiBaseUrl}/api/embed/start-embeding`,
  status: `${config.apiBaseUrl}/api/status`,
  integration: `${config.apiBaseUrl}/api/integration`,
  integrationUpdate: `${config.apiBaseUrl}/api/integration/update`,
  integrationToggle: (name: string) =>
    `${config.apiBaseUrl}/api/integration/toggle?name=${name}`,
  scraper: (integrationType: string) =>
    `${config.apiBaseUrl}/api/scraper/start-scraper/${integrationType}`,
  websocket: (endpoint: string) => {
    // Convert HTTP to WebSocket protocol
    const baseUrl = config.apiBaseUrl;
    const wsUrl = baseUrl.replace(
      /^https?:/,
      baseUrl.startsWith("https:") ? "wss:" : "ws:"
    );
    return `${wsUrl}/ws/${endpoint}`;
  },
} as const;
