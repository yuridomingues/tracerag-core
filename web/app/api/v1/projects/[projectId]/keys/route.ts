import { NextResponse } from "next/server";
import { generateApiKey } from "@/lib/crypto";
import { createClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

export async function POST(
  request: Request,
  context: { params: Promise<{ projectId: string }> },
) {
  const { projectId } = await context.params;
  const supabase = await createClient();
  const { data: claims, error: authError } = await supabase.auth.getClaims();

  if (authError || !claims?.claims?.sub) {
    return NextResponse.json({ error: "Unauthorized." }, { status: 401 });
  }

  const { data: project } = await supabase.from("projects").select("id").eq("id", projectId).single();
  if (!project) return NextResponse.json({ error: "Project not found." }, { status: 404 });

  let requestedName = "CI key";
  try {
    const body = (await request.json()) as { name?: unknown };
    if (typeof body.name === "string" && body.name.trim()) {
      requestedName = body.name.trim().slice(0, 80);
    }
  } catch {}

  const generated = generateApiKey();
  const { error } = await supabase.from("api_keys").insert({
    project_id: projectId,
    name: requestedName,
    key_prefix: generated.prefix,
    key_hash: generated.hash,
  });

  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ token: generated.token, prefix: generated.prefix });
}
