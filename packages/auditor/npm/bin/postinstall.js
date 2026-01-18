/**
 * Post-install script for secrin-auditor npm package.
 * Checks Python availability and optionally pre-installs the Python package.
 */

const { execSync } = require("child_process");

function checkPython() {
  const commands = ["python3", "python"];

  for (const cmd of commands) {
    try {
      const version = execSync(`${cmd} --version 2>&1`, { encoding: "utf8" });
      if (
        version.includes("3.11") ||
        version.includes("3.12") ||
        version.includes("3.13")
      ) {
        console.log(`✅ Found ${version.trim()}`);
        return cmd;
      }
    } catch (e) {
      // Command not found
    }
  }
  return null;
}

console.log("");
console.log("🔍 Secrin Auditor - Checking requirements...");
console.log("");

const pythonCmd = checkPython();

if (!pythonCmd) {
  console.log("⚠️  Python 3.11+ not found.");
  console.log(
    "   Please install Python 3.11 or later before using secrin-audit."
  );
  console.log("");
  console.log("   Installation:");
  console.log("     macOS:   brew install python@3.11");
  console.log("     Ubuntu:  sudo apt install python3.11");
  console.log("     Windows: https://www.python.org/downloads/");
} else {
  console.log("");
  console.log("📝 Usage:");
  console.log("   1. Get a Gemini API key: https://aistudio.google.com/");
  console.log('   2. Set the key: export GEMINI_API_KEY="your-key"');
  console.log("   3. Run: npx secrin-audit ./docs ./src");
}

console.log("");
