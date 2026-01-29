
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

    // We only care about installation/update actions for now
    // 'code' might be used for user-to-server token exchange if needed in future, 
    // but for now we just verify we got the callback.
    
    // Save/Update the installation record
    const installation = await prisma.gitHubInstallation.upsert({
      where: {
        userId: session.user.id,
      },
      update: {
        installationId: parseInt(installation_id),
        accountLogin: null, // We might want to fetch this from GitHub API if we had the token, but optional for now
      },
      create: {
        userId: session.user.id,
        installationId: parseInt(installation_id),
      },
    });

    return NextResponse.json({ success: true, installation });
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
