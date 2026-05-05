export type AnalysisResult = {
  id: string;
  fileName: string;
  fileSizeKb: number;
  estimatedPages: number;
  confidence: number;
  parseMode?: "real" | "mock";
  textSample?: string;
  summary: string;
  verdict: string;
  insights: string[];
  premiumUnlock: string[];
  targetOutcome: string;
};

export function buildMockAnalysis(input: {
  fileName: string;
  fileSizeKb: number;
  targetOutcome: string;
}): AnalysisResult {
  const estimatedPages = Math.max(1, Math.min(24, Math.round(input.fileSizeKb / 75) || 1));
  const confidence = Math.max(71, Math.min(96, 72 + estimatedPages));
  const normalizedGoal = input.targetOutcome.trim() || "Highlight the operational blockers and next action.";

  return {
    id: `analysis-${Date.now()}`,
    fileName: input.fileName,
    fileSizeKb: input.fileSizeKb,
    estimatedPages,
    confidence,
    parseMode: "mock",
    verdict: estimatedPages > 10 ? "Escalate before approval" : "Proceed if pricing and ownership are confirmed",
    summary:
      estimatedPages > 10
        ? "The document appears broad enough to hide ownership gaps and ambiguous pricing terms. The recommended path is to escalate the highlighted sections before any commitment."
        : "The document looks manageable for a fast decision. The likely blockers are limited to a few clauses or missing specifics rather than structural risk.",
    insights: [
      `Primary objective extracted: ${normalizedGoal}`,
      `Estimated review load: ${estimatedPages} pages with ${input.fileSizeKb} KB of source content.`,
      "High-signal scan suggests one stakeholder summary and one risk escalation note are enough for the first workflow.",
    ],
    premiumUnlock: [
      "Download a stakeholder memo in shareable format.",
      "Unlock clause-by-clause risk scoring.",
      "Store repeat analyses in a searchable workspace.",
    ],
    targetOutcome: normalizedGoal,
  };
}

export function decodePayload(payload: string | undefined): AnalysisResult | null {
  if (!payload) {
    return null;
  }

  try {
    const decoded = decodeURIComponent(payload);
    return JSON.parse(decoded) as AnalysisResult;
  } catch {
    return null;
  }
}
