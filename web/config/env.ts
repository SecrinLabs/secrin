const env = {
  api: {
    url: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  app: {
    env: process.env.NODE_ENV || "development",
  },
} as const;

const validateEnv = () => {
  if (!env.api.url) {
    throw new Error("NEXT_PUBLIC_API_URL environment variable is required");
  }
};

// Validate environment variables in development
if (process.env.NODE_ENV === "development") {
  validateEnv();
}

export default env;
