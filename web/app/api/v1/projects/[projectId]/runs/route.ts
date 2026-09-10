import { NextResponse } from "next/server";
import { authorizeProjectApiKey } from "@/lib/api-key-auth";
import { executeRun } from "@/lib/runner";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(
  request: Request,
  context: { params: Promise<{ projectId: string }> },
) {
  const { projectId } = await context.params;
  let body: Record<string, unknown>;

  try {
    body = (await request.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: "Body must be valid JSON." }, { status: 400 });
  }

  const datasetId = typeof body.dataset_id === "string" ? body.dataset_id : "";
  const endpointId = typeof body.endpoint_id === "string" ? body.endpoint_id : "";
  if (!datasetId || !endpointId) {
    return NextResponse.json({ error: "dataset_id and endpoint_id are required." }, { status: 422 });
  }

  try {
    const admin = await authorizeProjectApiKey(request.headers.get("authorization"), projectId);
    const result = await executeRun(admin, {
      projectId,
      datasetId,
      endpointId,
      gitSha: typeof body.git_sha === "string" ? body.git_sha.slice(0, 80) : null,
      branch: typeof body.branch === "string" ? body.branch.slice(0, 160) : null,
      setAsBaseline: body.set_as_baseline === true,
    });

    return NextResponse.json(result, { status: result.gate.passed ? 200 : 409 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Run failed.";
    const unauthorized = message.includes("API key") || message.includes("bearer");
    return NextResponse.json({ error: message }, { status: unauthorized ? 401 : 400 });
  }
}
