import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

export async function requireUser() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getClaims();
  const userId = data?.claims?.sub;

  if (error || !userId) {
    redirect("/login");
  }

  return {
    supabase,
    userId: String(userId),
    email: typeof data.claims.email === "string" ? data.claims.email : null,
  };
}

export async function requireProject(projectId: string) {
  const auth = await requireUser();
  const { data: project, error } = await auth.supabase
    .from("projects")
    .select("id, name, slug, workspace_id, baseline_run_id")
    .eq("id", projectId)
    .single();

  if (error || !project) {
    redirect("/dashboard");
  }

  return { ...auth, project };
}
