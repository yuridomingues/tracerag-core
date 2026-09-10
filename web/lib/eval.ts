export type EvalCase = {
  must_include: string[];
  must_not_include: string[];
  expected_sources: string[];
};

export type CaseEvaluation = {
  keywordPass: boolean | null;
  sourceRecall: number | null;
};

export type RunMetrics = {
  totalCases: number;
  successRate: number;
  keywordPassRate: number | null;
  sourceRecall: number | null;
  p95LatencyMs: number | null;
};

export type GateSettings = {
  minSuccessRate: number;
  minKeywordPassRate: number;
  minSourceRecall: number;
  maxSuccessRateDrop: number;
  maxKeywordPassRateDrop: number;
  maxSourceRecallDrop: number;
  maxP95LatencyRegressionPct: number;
};

export type GateOutcome = {
  passed: boolean;
  reasons: string[];
};

export const DEFAULT_GATE: GateSettings = {
  minSuccessRate: 0.95,
  minKeywordPassRate: 0.95,
  minSourceRecall: 0.8,
  maxSuccessRateDrop: 0.05,
  maxKeywordPassRateDrop: 0.05,
  maxSourceRecallDrop: 0.1,
  maxP95LatencyRegressionPct: 0.5,
};

function normalize(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function sourceMatches(actual: string, expected: string): boolean {
  const a = normalize(actual).replace(/\\/g, "/");
  const e = normalize(expected).replace(/\\/g, "/");
  return a === e || a.endsWith(`/${e}`);
}

export function evaluateCase(
  answer: string,
  sources: string[],
  test: EvalCase,
): CaseEvaluation {
  const normalizedAnswer = normalize(answer);
  const hasKeywordRules =
    test.must_include.length > 0 || test.must_not_include.length > 0;

  const keywordPass = hasKeywordRules
    ? test.must_include.every((item) => normalizedAnswer.includes(normalize(item))) &&
      test.must_not_include.every((item) => !normalizedAnswer.includes(normalize(item)))
    : null;

  let sourceRecall: number | null = null;
  if (test.expected_sources.length > 0) {
    const hits = test.expected_sources.filter((expected) =>
      sources.some((actual) => sourceMatches(actual, expected)),
    ).length;
    sourceRecall = hits / test.expected_sources.length;
  }

  return { keywordPass, sourceRecall };
}

function average(values: number[]): number | null {
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function p95(values: number[]): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.max(0, Math.ceil(sorted.length * 0.95) - 1);
  return sorted[index];
}

export function aggregateMetrics(
  results: Array<{
    success: boolean;
    latencyMs: number | null;
    keywordPass: boolean | null;
    sourceRecall: number | null;
  }>,
): RunMetrics {
  const totalCases = results.length;
  const keywordChecks = results
    .filter((item) => item.keywordPass !== null)
    .map((item) => (item.keywordPass ? 1 : 0));
  const sourceChecks = results
    .map((item) => item.sourceRecall)
    .filter((item): item is number => item !== null);
  const latencies = results
    .map((item) => item.latencyMs)
    .filter((item): item is number => item !== null);

  return {
    totalCases,
    successRate:
      totalCases === 0
        ? 0
        : results.filter((item) => item.success).length / totalCases,
    keywordPassRate: average(keywordChecks),
    sourceRecall: average(sourceChecks),
    p95LatencyMs: p95(latencies),
  };
}

export function evaluateGate(
  current: RunMetrics,
  settings: GateSettings,
  baseline: RunMetrics | null,
): GateOutcome {
  const reasons: string[] = [];

  if (current.successRate < settings.minSuccessRate) {
    reasons.push(
      `Success rate ${current.successRate.toFixed(3)} is below ${settings.minSuccessRate.toFixed(3)}.`,
    );
  }

  if (
    current.keywordPassRate !== null &&
    current.keywordPassRate < settings.minKeywordPassRate
  ) {
    reasons.push(
      `Keyword pass rate ${current.keywordPassRate.toFixed(3)} is below ${settings.minKeywordPassRate.toFixed(3)}.`,
    );
  }

  if (
    current.sourceRecall !== null &&
    current.sourceRecall < settings.minSourceRecall
  ) {
    reasons.push(
      `Source recall ${current.sourceRecall.toFixed(3)} is below ${settings.minSourceRecall.toFixed(3)}.`,
    );
  }

  if (baseline) {
    if (
      baseline.successRate - current.successRate >
      settings.maxSuccessRateDrop
    ) {
      reasons.push("Success rate regressed beyond the configured baseline tolerance.");
    }

    if (
      baseline.keywordPassRate !== null &&
      current.keywordPassRate !== null &&
      baseline.keywordPassRate - current.keywordPassRate >
        settings.maxKeywordPassRateDrop
    ) {
      reasons.push("Keyword pass rate regressed beyond the configured baseline tolerance.");
    }

    if (
      baseline.sourceRecall !== null &&
      current.sourceRecall !== null &&
      baseline.sourceRecall - current.sourceRecall >
        settings.maxSourceRecallDrop
    ) {
      reasons.push("Source recall regressed beyond the configured baseline tolerance.");
    }

    if (
      baseline.p95LatencyMs !== null &&
      baseline.p95LatencyMs > 0 &&
      current.p95LatencyMs !== null
    ) {
      const regression =
        (current.p95LatencyMs - baseline.p95LatencyMs) /
        baseline.p95LatencyMs;
      if (regression > settings.maxP95LatencyRegressionPct) {
        reasons.push("P95 latency regressed beyond the configured baseline tolerance.");
      }
    }
  }

  return { passed: reasons.length === 0, reasons };
}
