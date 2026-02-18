export const CONTENT = {
  hero: {
    heading: "Generate documentation for any codebase",
    subheading:
      "Paste a GitHub repo URL. Get Arc42 architecture docs, C4 diagrams, and Diataxis guides in minutes.",
  },
  generateForm: {
    placeholder: "https://github.com/owner/repo",
    submitLabel: "Generate",
    steps: [
      { key: "analyzing", label: "Analyzing repository" },
      { key: "arc42", label: "Generating Arc42 architecture docs", hasSubsteps: true, substepTotal: 12 },
      { key: "diagrams", label: "Generating C4 diagrams", hasSubsteps: true, substepTotal: 4 },
      { key: "diataxis", label: "Generating Diataxis guides", hasSubsteps: true, substepTotal: 4 },
      { key: "citations", label: "Adding provenance & citations" },
      { key: "finalizing", label: "Finalizing documentation" },
      { key: "writing_local", label: "Writing local docs" },
    ],
    successMessage: "Documentation generated successfully",
    errorFallback: "Generation failed.",
    connectionError: "Could not connect to the server.",
    statusError: "Failed to check generation status.",
    serverLostError: "Lost connection to the server.",
    serviceError:
      "Failed to connect to generation service. Make sure arc42gen-api and arc42gen-worker are running.",
    tryAgain: "Try again",
    generateAnother: "Generate another",
    generatedFiles: "Generated files",
  },
  features: {
    heading: "What gets generated",
    cards: [
      {
        title: "Arc42 Architecture",
        description:
          "12 sections covering system goals, constraints, building blocks, runtime behavior, deployment, and architecture decisions.",
        icon: "BookOpen" as const,
      },
      {
        title: "C4 Diagrams",
        description:
          "Four levels of architecture diagrams — context, container, component, and code — rendered as Mermaid diagrams.",
        icon: "Layers" as const,
      },
      {
        title: "Diataxis Guides",
        description:
          "Tutorials, how-to guides, reference docs, and explanations following the Diataxis documentation framework.",
        icon: "GitBranch" as const,
      },
    ],
  },
  cli: {
    heading: "Prefer the CLI?",
    terminalLabel: "terminal",
    commands: `poetry install
export GEMINI_API_KEY="your-key"
poetry run secrin generate https://github.com/owner/repo`,
  },
  login: {
    heading: "Welcome back",
    subheading: "Sign in to your account to continue",
    githubButton: "Sign in with GitHub",
    footer:
      "By clicking continue, you agree to our Terms of Service and Privacy Policy.",
    termsLink: "#",
    privacyLink: "#",
  },
} as const;
