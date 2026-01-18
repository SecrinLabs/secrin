#!/usr/bin/env node

/**
 * Secrin Auditor CLI - Node.js wrapper
 *
 * This wrapper calls the Python CLI under the hood.
 * Requires Python 3.11+ and GEMINI_API_KEY environment variable.
 */

const { execSync, spawn } = require("child_process");
const path = require("path");

// Check if Python is available
function getPythonCommand() {
  const commands = ["python3", "python"];

  for (const cmd of commands) {
    try {
      const version = execSync(`${cmd} --version 2>&1`, { encoding: "utf8" });
      if (
        version.includes("3.11") ||
        version.includes("3.12") ||
        version.includes("3.13")
      ) {
        return cmd;
      }
    } catch (e) {
      // Command not found, try next
    }
  }
  return null;
}

// Check if secrin-auditor is installed
function isAuditorInstalled(pythonCmd) {
  try {
    execSync(`${pythonCmd} -c "import secrin_auditor" 2>&1`, {
      encoding: "utf8",
    });
    return true;
  } catch (e) {
    return false;
  }
}

// Install the Python package
function installAuditor(pythonCmd) {
  console.log("📦 Installing secrin-auditor Python package...");
  try {
    execSync(`${pythonCmd} -m pip install secrin-auditor --quiet`, {
      stdio: "inherit",
    });
    return true;
  } catch (e) {
    console.error("Failed to install secrin-auditor. Please install manually:");
    console.error("  pip install secrin-auditor");
    return false;
  }
}

// Main
async function main() {
  const args = process.argv.slice(2);

  // Show help if no args
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.log(`
Secrin Auditor - AI-powered documentation drift detection

Usage:
  secrin-audit <docs_folder> <repo_folder> [options]

Arguments:
  docs_folder    Path to your documentation folder (e.g., ./docs)
  repo_folder    Path to your codebase (e.g., ./src or .)

Options:
  -v, --verbose  Show verbose output
  -h, --help     Show this help message

Environment:
  GEMINI_API_KEY  Your Google Gemini API key (required)
                  Get one at: https://aistudio.google.com/

Examples:
  secrin-audit ./docs ./src
  secrin-audit ./documentation . --verbose

Exit Codes:
  0  All documentation is accurate
  1  One or more documents have drifted from code
`);
    process.exit(0);
  }

  // Check for API key
  if (!process.env.GEMINI_API_KEY) {
    console.error("❌ Error: GEMINI_API_KEY environment variable is not set.");
    console.error("");
    console.error("Get your free API key from: https://aistudio.google.com/");
    console.error("Then set it:");
    console.error('  export GEMINI_API_KEY="your-key-here"');
    process.exit(1);
  }

  // Find Python
  const pythonCmd = getPythonCommand();
  if (!pythonCmd) {
    console.error("❌ Error: Python 3.11+ is required but not found.");
    console.error("");
    console.error("Please install Python 3.11 or later:");
    console.error("  macOS: brew install python@3.11");
    console.error("  Ubuntu: sudo apt install python3.11");
    console.error("  Windows: https://www.python.org/downloads/");
    process.exit(1);
  }

  // Check/install auditor
  if (!isAuditorInstalled(pythonCmd)) {
    if (!installAuditor(pythonCmd)) {
      process.exit(1);
    }
  }

  // Run the auditor
  const child = spawn(pythonCmd, ["-m", "secrin_auditor.cli", ...args], {
    stdio: "inherit",
    env: process.env,
  });

  child.on("close", (code) => {
    process.exit(code || 0);
  });

  child.on("error", (err) => {
    console.error("Failed to run auditor:", err.message);
    process.exit(1);
  });
}

main();
