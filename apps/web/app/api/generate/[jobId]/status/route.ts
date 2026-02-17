import { NextRequest, NextResponse } from "next/server";

const ARC42GEN_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;

  try {
    const res = await fetch(`${ARC42GEN_API}/jobs/${jobId}`);

    if (!res.ok) {
      return NextResponse.json(
        { error: "Job not found" },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Job status error:", error);
    return NextResponse.json(
      { error: "Failed to connect to generation service" },
      { status: 502 }
    );
  }
}
