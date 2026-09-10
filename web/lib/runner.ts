import type { SupabaseClient } from "@supabase/supabase-js";

import { decryptSecret } from "@/lib/crypto";
import {
  aggregateMetrics,
  DEFAULT_GATE,
  evaluateCase,
  evaluateGate,
  type GateSettings,
  type RunMetrics,
} from "@/lib/eval";
import {
  getStringArrayAtPath,
  getStringAtPath,
  setAtPath,
} from "@/lib/json-path";
import { postJsonSafely } from "@/lib/safe-http";

type ExecuteRunInput = {
  projectId: string;
  datasetId: string;
  endpointId: string;
  triggeredBy?: string | null;
  gitSha?: string | null;
  branch?: string | null;
  setAsBaseline?: boolean;
};

type EndpointRow = {
  id: string;
  url: string;
  question_path: string;
  response_text_path: string;
  response_sources_path: string | null;
  auth_header_name: string | null;
  auth_secret_ciphertext: string | null;
};

type CaseRow = {
  id: string;
  question: string;
  must_include: string[] | null;
  must_not_include: string[] | null;
  expected_sources: string[] | null;
};

function gateSettings(row: Record<string, unknown> | null): GateSettings {
  if (!row) return DEFAULT_GATE;

  const number = (key: string, fallback: number) => {
    const value = row[key];
    return typeof value === "number" ? value : Number(value ?? fallback);
  };

  return {
    minSuccessRate: number("min_success_rate", DEFAULT_GATE.minSuccessRate),
    minKeywordPassRate: number(
      "min_keyword_pass_rate",
      DEFAULT_GATE.minKeywordPassRate,
    ),
    minSourceRecall: number("min_source_recall", DEFAULT_GATE.minSourceRecall),
    maxSuccessRateDrop: number(
      "max_success_rate_drop",
      DEFAULT_GATE.maxSuccessRateDrop,
    ),
    maxKeywordPassRateDrop: number(
      "max_keyword_pass_rate_drop",
      DEFAULT_GATE.maxKeywordPassRateDrop,
    ),
    maxSourceRecallDrop: number(
      "max_source_recall_drop",
      DEFAULT_GATE.maxSourceRecallDrop,
    ),
    maxP95LatencyRegressionPct: number(
      "max_p95_latency_regression_pct",
      DEFAULT_GATE.maxP95LatencyRegressionPct,
    ),
  };
}

function metricsFromRow(row: Record<string, unknown> | null): RunMetrics | null {
  if (!row) return null;

  const nullable = (value: unknown) =>
    value === null || value === undefined ? null : Number(value);

  return {
    totalCases: Number(row.total_cases ?? 0),
    successRate: Number(row.success_rate ?? 0),
    keywordPassRate: nullable(row.keyword_pass_rate),
    sourceRecall: nullable(row.source_recall),
    p95LatencyMs: nullable(row.p95_latency_ms),
  };
}

async function mapConcurrent<T, R>(
  values: T[],
  concurrency: number,
  worker: (value: T) => Promise<R>,
): Promise<R[]> {
  const output = new Array<R>(values.length);
  let cursor = 0;

  async function runWorker() {
    while (true) {
      const index = cursor++;
      if (index >= values.length) return;
      output[index] = await worker(values[index]);
    }
  }

  const workers = Array.from(
    { length: Math.min(concurrency, values.length) },
    () => runWorker(),
  );
  await Promise.all(workers);
  return output;
}

export async function executeRun(
  admin: SupabaseClient,
  input: ExecuteRunInput,
) {
  const { data: project, error: projectError } = await admin
    .from("projects")
    .select("id, baseline_run_id")
    .eq("id", input.projectId)
    .single();

  if (projectError || !project) {
    throw new Error("Project not found.");
  }

  const [{ data: endpoint, error: endpointError }, { data: cases, error: casesError }] =
    await Promise.all([
      admin
        .from("rag_endpoints")
        .select(
          "id, url, question_path, response_text_path, response_sources_path, auth_header_name, auth_secret_ciphertext",
        )
        .eq("id", input.endpointId)
        .eq("project_id", input.projectId)
        .single(),
      admin
        .from("eval_cases")
        .select(
          "id, question, must_include, must_not_include, expected_sources, datasets!inner(project_id)",
        )
        .eq("dataset_id", input.datasetId)
        .eq("datasets.project_id", input.projectId)
        .order("created_at", { ascending: true }),
    ]);

  if (endpointError || !endpoint) {
    throw new Error("RAG endpoint not found.");
  }
  if (casesError) {
    throw new Error(`Could not load evaluation cases: ${casesError.message}`);
  }

  const typedCases = (cases ?? []) as unknown as CaseRow[];
  if (!typedCases.length) {
    throw new Error("Dataset has no evaluation cases.");
  }
  if (typedCases.length > 25) {
    throw new Error("Alpha runs are limited to 25 cases.");
  }

  const { data: run, error: runError } = await admin
    .from("eval_runs")
    .insert({
      project_id: input.projectId,
      dataset_id: input.datasetId,
      endpoint_id: input.endpointId,
      baseline_run_id: project.baseline_run_id,
      triggered_by: input.triggeredBy ?? null,
      status: "running",
      git_sha: input.gitSha ?? null,
      branch: input.branch ?? null,
      started_at: new Date().toISOString(),
    })
    .select("id")
    .single();

  if (runError || !run) {
    throw new Error(`Could not create run: ${runError?.message ?? "unknown error"}`);
  }

  try {
    const endpointRow = endpoint as EndpointRow;
    const authSecret = endpointRow.auth_secret_ciphertext
      ? decryptSecret(endpointRow.auth_secret_ciphertext)
      : null;

    const results = await mapConcurrent(typedCases, 4, async (testCase) => {
      try {
        const headers: Record<string, string> = {
          accept: "application/json",
          "content-type": "application/json",
          "user-agent": "TraceRAG/0.3",
        };

        if (endpointRow.auth_header_name && authSecret) {
          headers[endpointRow.auth_header_name] = authSecret;
        }

        const response = await postJsonSafely(
          endpointRow.url,
          setAtPath(endpointRow.question_path, testCase.question),
          headers,
        );

        const answer =
          getStringAtPath(response.body, endpointRow.response_text_path) ?? "";
        const sources = endpointRow.response_sources_path
          ? getStringArrayAtPath(response.body, endpointRow.response_sources_path)
          : [];
        const evaluation = evaluateCase(answer, sources, {
          must_include: testCase.must_include ?? [],
          must_not_include: testCase.must_not_include ?? [],
          expected_sources: testCase.expected_sources ?? [],
        });

        const success =
          response.status >= 200 && response.status < 300 && answer.length > 0;

        return {
          caseId: testCase.id,
          success,
          httpStatus: response.status,
          latencyMs: response.latencyMs,
          answer,
          sources,
          keywordPass: evaluation.keywordPass,
          sourceRecall: evaluation.sourceRecall,
          error: success ? null : "Endpoint response was not a successful answer.",
        };
      } catch (error) {
        return {
          caseId: testCase.id,
          success: false,
          httpStatus: null,
          latencyMs: null,
          answer: "",
          sources: [] as string[],
          keywordPass: null,
          sourceRecall: null,
          error: error instanceof Error ? error.message : "Unknown endpoint error.",
        };
      }
    });

    const metrics = aggregateMetrics(results);

    const [{ data: settingsRow }, { data: baselineRow }] = await Promise.all([
      admin
        .from("project_gate_settings")
        .select("*")
        .eq("project_id", input.projectId)
        .maybeSingle(),
      project.baseline_run_id
        ? admin
            .from("eval_runs")
            .select(
              "total_cases, success_rate, keyword_pass_rate, source_recall, p95_latency_ms",
            )
            .eq("id", project.baseline_run_id)
            .maybeSingle()
        : Promise.resolve({ data: null }),
    ]);

    const gate = evaluateGate(
      metrics,
      gateSettings((settingsRow ?? null) as Record<string, unknown> | null),
      metricsFromRow((baselineRow ?? null) as Record<string, unknown> | null),
    );

    const { error: resultsError } = await admin.from("eval_results").insert(
      results.map((result) => ({
        run_id: run.id,
        case_id: result.caseId,
        success: result.success,
        http_status: result.httpStatus,
        latency_ms: result.latencyMs,
        response_text: result.answer,
        sources: result.sources,
        keyword_pass: result.keywordPass,
        source_recall: result.sourceRecall,
        error: result.error,
      })),
    );

    if (resultsError) {
      throw new Error(`Could not store case results: ${resultsError.message}`);
    }

    const completedAt = new Date().toISOString();
    const { error: updateError } = await admin
      .from("eval_runs")
      .update({
        status: "completed",
        total_cases: metrics.totalCases,
        success_rate: metrics.successRate,
        keyword_pass_rate: metrics.keywordPassRate,
        source_recall: metrics.sourceRecall,
        p95_latency_ms: metrics.p95LatencyMs,
        gate_passed: gate.passed,
        gate_reasons: gate.reasons,
        completed_at: completedAt,
      })
      .eq("id", run.id);

    if (updateError) {
      throw new Error(`Could not finalize run: ${updateError.message}`);
    }

    if (input.setAsBaseline && gate.passed) {
      const { error: baselineError } = await admin
        .from("projects")
        .update({ baseline_run_id: run.id })
        .eq("id", input.projectId);

      if (baselineError) {
        throw new Error(`Could not set baseline: ${baselineError.message}`);
      }
    }

    return {
      id: run.id,
      status: "completed" as const,
      metrics,
      gate,
      baselineRunId: project.baseline_run_id as string | null,
      setAsBaseline: Boolean(input.setAsBaseline && gate.passed),
    };
  } catch (error) {
    await admin
      .from("eval_runs")
      .update({
        status: "failed",
        gate_passed: false,
        gate_reasons: [
          error instanceof Error ? error.message : "Unknown run failure.",
        ],
        completed_at: new Date().toISOString(),
      })
      .eq("id", run.id);

    throw error;
  }
}
