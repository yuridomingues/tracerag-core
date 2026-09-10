"use server";

import { randomBytes } from "node:crypto";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { requireProject, requireUser } from "@/lib/auth";
import { encryptSecret } from "@/lib/crypto";
import { executeRun } from "@/lib/runner";
import { createAdminClient } from "@/lib/supabase/admin";

function slugify(value: string) {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 48);
}

function lines(value: FormDataEntryValue | null): string[] {
  return String(value ?? "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 20);
}

function dashboardError(message: string): never {
  redirect(`/dashboard?error=${encodeURIComponent(message)}`);
}

function projectError(projectId: string, message: string): never {
  redirect(`/dashboard/projects/${projectId}?error=${encodeURIComponent(message)}`);
}

export async function signOutAction() {
  const { supabase } = await requireUser();
  await supabase.auth.signOut();
  redirect("/");
}

export async function createWorkspaceAction(formData: FormData) {
  const { supabase, userId } = await requireUser();
  const name = String(formData.get("name") ?? "").trim();
  if (name.length < 2 || name.length > 80) {
    dashboardError("Workspace name must contain 2 to 80 characters.");
  }

  const slug = `${slugify(name) || "workspace"}-${randomBytes(3).toString("hex")}`;
  const { error } = await supabase.from("workspaces").insert({
    owner_id: userId,
    name,
    slug,
  });
  if (error) dashboardError(error.message);
  revalidatePath("/dashboard");
}

export async function createProjectAction(formData: FormData) {
  const { supabase } = await requireUser();
  const workspaceId = String(formData.get("workspace_id") ?? "");
  const name = String(formData.get("name") ?? "").trim();

  if (!workspaceId || name.length < 2 || name.length > 80) {
    dashboardError("Choose a workspace and enter a valid project name.");
  }

  const { data: workspace } = await supabase
    .from("workspaces").select("id").eq("id", workspaceId).single();
  if (!workspace) dashboardError("Workspace not found.");

  const slug = `${slugify(name) || "project"}-${randomBytes(3).toString("hex")}`;
  const { data: project, error } = await supabase
    .from("projects")
    .insert({ workspace_id: workspaceId, name, slug })
    .select("id")
    .single();

  if (error || !project) dashboardError(error?.message ?? "Could not create project.");
  redirect(`/dashboard/projects/${project.id}`);
}

export async function createDatasetAction(formData: FormData) {
  const projectId = String(formData.get("project_id") ?? "");
  const name = String(formData.get("name") ?? "").trim();
  const { supabase } = await requireProject(projectId);

  if (name.length < 2 || name.length > 100) {
    projectError(projectId, "Dataset name must contain 2 to 100 characters.");
  }

  const { error } = await supabase.from("datasets").insert({ project_id: projectId, name });
  if (error) projectError(projectId, error.message);
  revalidatePath(`/dashboard/projects/${projectId}`);
}

export async function createCaseAction(formData: FormData) {
  const projectId = String(formData.get("project_id") ?? "");
  const datasetId = String(formData.get("dataset_id") ?? "");
  const question = String(formData.get("question") ?? "").trim();
  const { supabase } = await requireProject(projectId);

  if (!datasetId || question.length < 3 || question.length > 2000) {
    projectError(projectId, "Choose a dataset and enter a valid question.");
  }

  const { data: dataset } = await supabase
    .from("datasets")
    .select("id")
    .eq("id", datasetId)
    .eq("project_id", projectId)
    .single();
  if (!dataset) projectError(projectId, "Dataset not found.");

  const { error } = await supabase.from("eval_cases").insert({
    dataset_id: datasetId,
    question,
    must_include: lines(formData.get("must_include")),
    must_not_include: lines(formData.get("must_not_include")),
    expected_sources: lines(formData.get("expected_sources")),
  });
  if (error) projectError(projectId, error.message);
  revalidatePath(`/dashboard/projects/${projectId}`);
}

export async function createEndpointAction(formData: FormData) {
  const projectId = String(formData.get("project_id") ?? "");
  const { supabase } = await requireProject(projectId);
  const name = String(formData.get("name") ?? "").trim();
  const endpointUrl = String(formData.get("url") ?? "").trim();
  const questionPath = String(formData.get("question_path") ?? "question").trim();
  const responseTextPath = String(formData.get("response_text_path") ?? "answer").trim();
  const responseSourcesPath = String(formData.get("response_sources_path") ?? "sources").trim();
  const authHeaderName = String(formData.get("auth_header_name") ?? "").trim();
  const authSecret = String(formData.get("auth_secret") ?? "");

  let parsed: URL;
  try {
    parsed = new URL(endpointUrl);
  } catch {
    projectError(projectId, "Endpoint URL is invalid.");
  }

  if (parsed.protocol !== "https:") {
    projectError(projectId, "TraceRAG only accepts HTTPS endpoints.");
  }
  if (!name || !questionPath || !responseTextPath) {
    projectError(projectId, "Endpoint name and JSON paths are required.");
  }
  if (Boolean(authHeaderName) !== Boolean(authSecret)) {
    projectError(projectId, "Provide both an auth header name and value, or leave both empty.");
  }

  const { error } = await supabase.from("rag_endpoints").insert({
    project_id: projectId,
    name,
    url: endpointUrl,
    question_path: questionPath,
    response_text_path: responseTextPath,
    response_sources_path: responseSourcesPath || null,
    auth_header_name: authHeaderName || null,
    auth_secret_ciphertext: authSecret ? encryptSecret(authSecret) : null,
  });
  if (error) projectError(projectId, error.message);
  revalidatePath(`/dashboard/projects/${projectId}`);
}

export async function runDatasetAction(formData: FormData) {
  const projectId = String(formData.get("project_id") ?? "");
  const datasetId = String(formData.get("dataset_id") ?? "");
  const endpointId = String(formData.get("endpoint_id") ?? "");
  const setAsBaseline = formData.get("set_as_baseline") === "on";
  const { supabase, userId } = await requireProject(projectId);

  const [{ data: dataset }, { data: endpoint }] = await Promise.all([
    supabase.from("datasets").select("id").eq("id", datasetId).eq("project_id", projectId).single(),
    supabase.from("rag_endpoints").select("id").eq("id", endpointId).eq("project_id", projectId).single(),
  ]);
  if (!dataset || !endpoint) projectError(projectId, "Dataset or endpoint not found.");

  try {
    const result = await executeRun(createAdminClient(), {
      projectId,
      datasetId,
      endpointId,
      triggeredBy: userId,
      setAsBaseline,
    });
    redirect(`/dashboard/projects/${projectId}?run=${result.id}`);
  } catch (error) {
    projectError(projectId, error instanceof Error ? error.message : "Could not execute run.");
  }
}
