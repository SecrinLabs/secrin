import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { prisma } from "@/lib/prisma";

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

/**
 * GET /api/projects/[id]/regenerate/status
 * Poll the status of a doc generation job
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user?.id) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id: projectId } = await params;

    const project = await prisma.project.findFirst({
      where: {
        id: projectId,
        userId: session.user.id,
      },
      select: {
        docGenStatus: true,
        docGenJobId: true,
        lastDocGenAt: true,
      },
    });

    if (!project) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    // If no job ID, just return the stored status
    if (!project.docGenJobId) {
      return NextResponse.json({
        status: project.docGenStatus || "idle",
        progress: 0,
        current_step: null,
        error: null,
      });
    }

    // Poll the arc42gen API for job status
    const statusResponse = await fetch(
      `${NEXT_PUBLIC_API_URL}/jobs/${project.docGenJobId}`,
      { signal: AbortSignal.timeout(5_000) }
    );

    if (!statusResponse.ok) {
      return NextResponse.json({
        status: project.docGenStatus || "unknown",
        progress: 0,
        current_step: null,
        error: "Could not fetch job status",
      });
    }

    const jobStatus = await statusResponse.json();

    // Update project status if job has completed
    if (jobStatus.status === "success" && project.docGenStatus !== "success") {
      await prisma.project.update({
        where: { id: projectId },
        data: {
          docGenStatus: "success",
          lastDocGenAt: new Date(),
        },
      });
    } else if (jobStatus.status === "failed" && project.docGenStatus !== "failed") {
      await prisma.project.update({
        where: { id: projectId },
        data: { docGenStatus: "failed" },
      });
    }

    return NextResponse.json({
      status: jobStatus.status,
      progress: jobStatus.progress,
      current_step: jobStatus.current_step,
      step_number: jobStatus.step_number ?? null,
      total_steps: jobStatus.total_steps ?? null,
      substep: jobStatus.substep ?? null,
      substep_total: jobStatus.substep_total ?? null,
      substep_message: jobStatus.substep_message ?? null,
      error: jobStatus.error,
      result: jobStatus.result,
    });

  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to get job status" },
      { status: 500 }
    );
  }
}
