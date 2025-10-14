const env = {
  api: {
    url: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  app: {
    env: process.env.NODE_ENV || "development",
  },
  discord: {
    clientId: process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID || "",
    permissions: process.env.NEXT_PUBLIC_DISCORD_PERMISSIONS || "",
    integrationType: process.env.NEXT_PUBLIC_DISCORD_INTEGRATION_TYPE || "",
    scope: process.env.NEXT_PUBLIC_DISCORD_SCOPE || "",
    redirectUri: process.env.NEXT_PUBLIC_DISCORD_REDIRECT_URI || "",
    responseType: process.env.NEXT_PUBLIC_DISCORD_RESPONSE_TYPE || "",
  },
  github: {
    app_url: process.env.GITHUB_APP_URL || "",
  },
} as const;

const validateEnv = () => {
  if (!env.api.url) {
    throw new Error("NEXT_PUBLIC_API_URL environment variable is required");
  }

  if (!env.discord.clientId) {
    throw new Error("NEXT_PUBLIC_DISCORD_CLIENT_ID is required");
  }
};

// Validate only in development
if (process.env.NODE_ENV === "development") {
  validateEnv();
}

export default env;
