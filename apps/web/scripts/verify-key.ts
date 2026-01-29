
import "dotenv/config";
import { createAppAuth } from "@octokit/auth-app";

async function verify() {
  const appId = process.env.GITHUB_APP_ID;
  const privateKey = process.env.GITHUB_APP_PRIVATE_KEY;

  console.log("--- Debugging GitHub App Credentials ---");
  console.log(`App ID present: ${!!appId}`);
  console.log(`Private Key present: ${!!privateKey}`);

  if (!privateKey) {
    console.error("❌ Private Key is missing from .env");
    return;
  }

  let formattedKey = privateKey.replace(/\\n/g, "\n");
  if (formattedKey.startsWith('"') && formattedKey.endsWith('"')) {
    formattedKey = formattedKey.slice(1, -1);
  }
  formattedKey = formattedKey.trim();

  console.log(`Key Length: ${formattedKey.length} chars`);
  
  if (formattedKey.length < 100) {
      console.error("❌ Key is suspiciously short (< 100 chars). It is likely a Client Secret, not a Private Key.");
      return;
  }

  if (!formattedKey.includes("BEGIN RSA PRIVATE KEY")) {
      console.error("❌ Key missing PEM header.");
  }

  try {
    const auth = createAppAuth({
      appId: appId || "dummy-id",
      privateKey: formattedKey,
    });
    
    // Attempt to create a JWT (locally) - this doesn't hit GitHub API but checks key validity for signing
    const jwt = await auth({ type: "app" });
    console.log("✅ Private Key is valid! Successfully generated JWT.");
    console.log("JWT prefix:", jwt.token.substring(0, 10) + "...");
  } catch (error: any) {
    console.error("❌ Failed to sign JWT with this key.");
    console.error("Error:", error.message);
    if (error.code) console.error("Code:", error.code);
  }
}

verify();
