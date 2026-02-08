import { prisma } from "@/lib/prisma";

interface TokenResult {
  accessToken: string;
  error?: never;
}

interface TokenError {
  accessToken?: never;
  error: string;
}

type GetTokenResult = TokenResult | TokenError;

/**
 * Get a valid GitHub access token for a user.
 * If the current token is expired, it will be refreshed automatically.
 * 
 * @param userId - The user's ID
 * @returns The access token or an error message
 */
export async function getValidAccessToken(userId: string): Promise<GetTokenResult> {
  const installation = await prisma.gitHubInstallation.findUnique({
    where: { userId },
  });

  if (!installation) {
    return { error: "GitHub App not installed" };
  }

  if (!installation.accessToken) {
    return { error: "No access token found. Please reinstall the GitHub App." };
  }

  // Check if token is expired (with 5-minute buffer to be safe)
  const now = new Date();
  const bufferMs = 5 * 60 * 1000; // 5 minutes
  const isExpired = installation.tokenExpiresAt && 
    installation.tokenExpiresAt.getTime() <= now.getTime() + bufferMs;

  if (!isExpired) {
    return { accessToken: installation.accessToken };
  }

  // Token is expired - try to refresh it
  if (!installation.refreshToken) {
    return { error: "Token expired and no refresh token available. Please reinstall the GitHub App." };
  }

  console.log(`Token expired for user ${userId}, refreshing...`);

  const clientId = process.env.GITHUB_APP_CLIENTID;
  const clientSecret = process.env.GITHUB_APP_SECRET;

  if (!clientId || !clientSecret) {
    return { error: "GitHub App not configured properly" };
  }

  try {
    const response = await fetch("https://github.com/login/oauth/access_token", {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        client_id: clientId,
        client_secret: clientSecret,
        grant_type: "refresh_token",
        refresh_token: installation.refreshToken,
      }),
    });

    const tokenData = await response.json();

    if (tokenData.error) {
      console.error("GitHub token refresh error:", tokenData);
      // Refresh token may have expired (6 months) - user needs to reinstall
      return { error: `Token refresh failed: ${tokenData.error_description || tokenData.error}. Please reinstall the GitHub App.` };
    }

    const newAccessToken = tokenData.access_token;
    const newRefreshToken = tokenData.refresh_token;
    const expiresIn = tokenData.expires_in; // seconds

    if (!newAccessToken) {
      return { error: "No access token in refresh response" };
    }

    // Calculate new expiry time
    const tokenExpiresAt = new Date(Date.now() + expiresIn * 1000);

    // Update the installation with new tokens
    await prisma.gitHubInstallation.update({
      where: { userId },
      data: {
        accessToken: newAccessToken,
        refreshToken: newRefreshToken || installation.refreshToken, // GitHub may or may not return a new refresh token
        tokenExpiresAt,
      },
    });

    console.log(`Token refreshed for user ${userId}, expires at ${tokenExpiresAt.toISOString()}`);

    return { accessToken: newAccessToken };
  } catch (error: any) {
    console.error("Error refreshing GitHub token:", error);
    return { error: `Failed to refresh token: ${error.message}` };
  }
}

/**
 * Get a valid access token from a GitHubInstallation object.
 * Use this when you already have the installation data loaded.
 * 
 * @param installation - The GitHubInstallation object
 * @returns The access token or an error message
 */
export async function getValidAccessTokenFromInstallation(
  installation: {
    userId: string;
    accessToken: string | null;
    refreshToken?: string | null;
    tokenExpiresAt?: Date | null;
    [key: string]: unknown; // Allow additional properties from Prisma
  } | null | undefined
): Promise<GetTokenResult> {
  if (!installation) {
    return { error: "GitHub App not installed" };
  }

  if (!installation.accessToken) {
    return { error: "No access token found. Please reinstall the GitHub App." };
  }

  // Check if token is expired (with 5-minute buffer)
  const now = new Date();
  const bufferMs = 5 * 60 * 1000;
  const isExpired = installation.tokenExpiresAt && 
    installation.tokenExpiresAt.getTime() <= now.getTime() + bufferMs;

  if (!isExpired) {
    return { accessToken: installation.accessToken };
  }

  // Token is expired - delegate to the main function which handles refresh
  return getValidAccessToken(installation.userId);
}
