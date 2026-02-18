import { NextRequest, NextResponse } from "next/server";

const ARC42GEN_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const DOCS_OUTPUT_DIR = process.env.DOCS_OUTPUT_DIR || "./docs";

export async function POST(req: NextRequest) {
  try {
    const { repo_url } = await req.json();

    if (!repo_url || typeof repo_url !== "string") {
      return NextResponse.json(
        { error: "repo_url is required" },
        { status: 400 }
      );
    }

    const res = await fetch(`${ARC42GEN_API}/public/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_repo_url: repo_url,
        local_output_dir: DOCS_OUTPUT_DIR,
      }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => null);
      return NextResponse.json(
        { error: body?.detail || "Failed to start generation" },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json({ job_id: data.job_id, status: data.status });
  } catch (error) {
    console.error("Generate API error:", error);
    return NextResponse.json(
      { error: "Failed to connect to generation service. Make sure arc42gen-api and arc42gen-worker are running." },
      { status: 502 }
    );
  }
}
