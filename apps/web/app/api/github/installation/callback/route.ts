
import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { prisma } from "@/lib/prisma";

export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { installation_id, setup_action, code } = await req.json();

    if (!installation_id) {
      return NextResponse.json(
        { error: "Missing installation_id" },
        { status: 400 }
      );
    }

    if (!code) {
      return NextResponse.json(
        { error: "Missing code parameter" },
        { status: 400 }
      );
    }

    // Exchange the code for a user access token
    // This is the OAuth flow - code is one-time use and must be exchanged
    const clientId = process.env.GITHUB_APP_CLIENTID;
    const clientSecret = process.env.GITHUB_APP_SECRET;

    if (!clientId || !clientSecret) {
      console.error("Missing GITHUB_APP_CLIENTID or GITHUB_APP_SECRET");
      return NextResponse.json(
        { error: "GitHub App not configured" },
        { status: 500 }
      );
    }

    const tokenResponse = await fetch("https://github.com/login/oauth/access_token", {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        client_id: clientId,
        client_secret: clientSecret,
        code: code,
      }),
    });

    const tokenData = await tokenResponse.json();

    if (tokenData.error) {
      console.error("GitHub OAuth error:", tokenData);
      return NextResponse.json(
        { error: tokenData.error_description || "Failed to exchange code for token" },
        { status: 400 }
      );
    }

    const accessToken = tokenData.access_token; // This will be a ghu_* token
    const refreshToken = tokenData.refresh_token; // ghr_* refresh token
    const expiresIn = tokenData.expires_in; // seconds until expiry (8 hours = 28800)

    if (!accessToken) {
      console.error("No access_token in response:", tokenData);
      return NextResponse.json(
        { error: "No access token received" },
        { status: 500 }
      );
    }

    // Calculate token expiry time
    const tokenExpiresAt = expiresIn ? new Date(Date.now() + expiresIn * 1000) : null;

    // Save/Update the installation record with the REAL access token and refresh token
    const installation = await prisma.gitHubInstallation.upsert({
      where: {
        userId: session.user.id,
      },
      update: {
        installationId: parseInt(installation_id),
        accessToken: accessToken,
        refreshToken: refreshToken || null,
        tokenExpiresAt: tokenExpiresAt,
        accountLogin: null,
      },
      create: {
        userId: session.user.id,
        installationId: parseInt(installation_id),
        accessToken: accessToken,
        refreshToken: refreshToken || null,
        tokenExpiresAt: tokenExpiresAt,
      },
    });

    return NextResponse.json({ success: true, installation: { id: installation.id } });
  } catch (error) {
    console.error("Error saving GitHub installation:", error);
    return NextResponse.json(
      { error: "Failed to save installation" },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const installation = await prisma.gitHubInstallation.findUnique({
      where: {
        userId: session.user.id,
      },
    });

    if (!installation) {
      return NextResponse.json({ installed: false, installationId: null });
    }

    return NextResponse.json({
      installed: true,
      installationId: installation.installationId,
    });
  } catch (error) {
    console.error("Error checking GitHub installation:", error);
    return NextResponse.json(
      { error: "Failed to check installation" },
      { status: 500 }
    );
  }
}
