export const GITHUB_CONFIG = {
  API_ENDPOINTS: {
    CONNECT: "/connect/github",
  },
  TEXT: {
    TITLE: "GitHub",
    DESCRIPTION: "Connect repositories to ingest code and commit history.",
    INPUT_LABEL: "Repository URL",
    INPUT_PLACEHOLDER: "https://github.com/owner/repo",
    BUTTON_CONNECT: "Connect Repository",
    BUTTON_CONNECTING: "Connecting...",
    SUCCESS_MESSAGE: (repoName: string) =>
      `Successfully connected to ${repoName}`,
    ERROR_EMPTY_URL: "Please enter a repository URL",
    ERROR_GENERIC: "Failed to connect repository",
    FOOTER_NOTE:
      "For live updates, please configure the GitHub App webhook in your repository settings.",
  },
} as const;
