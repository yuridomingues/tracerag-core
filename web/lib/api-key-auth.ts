import { hashApiKey } from "@/lib/crypto";
import { createAdminClient } from "@/lib/supabase/admin";

export async function authorizeProjectApiKey(
  authorization: string | null,
  projectId: string,
) {
  if (!authorization?.startsWith("Bearer ")) throw new Error("Missing bearer API key.");

  const token = authorization.slice("Bearer ".length).trim();
  if (!token.startsWith("trg_live_")) throw new Error("Invalid API key.");

  const admin = createAdminClient();
  const { data: key, error } = await admin
    .from("api_keys")
    .select("id, project_id, revoked_at")
    .eq("key_hash", hashApiKey(token))
    .maybeSingle();

  if (error || !key || key.revoked_at || key.project_id !== projectId) {
    throw new Error("Invalid or revoked API key.");
  }

  await admin.from("api_keys").update({ last_used_at: new Date().toISOString() }).eq("id", key.id);
  return admin;
}
