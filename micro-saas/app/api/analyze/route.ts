import { NextResponse } from "next/server";

import { appendAnalysisHistory } from "@/lib/analysis-history";
import { countAnalysesForUserOnDate } from "@/lib/analysis-history";
import { resolvePlanTier } from "@/lib/entitlements";
import { buildMockAnalysis } from "@/lib/mock-analysis";
import { extractPdfText } from "@/lib/pdf-extractor";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const RISK_MARKERS = ["penalty", "liability", "termination", "renewal", "exclusive", "delay", "sla", "breach", "fee"];

export const runtime = "nodejs";

export async function POST(request: Request) {
  const userId = request.headers.get("x-user-id")?.trim() || "anonymous";
  const plan = await resolvePlanTier(userId);
  const todayIso = new Date().toISOString().slice(0, 10);
  const usedToday = await countAnalysesForUserOnDate(userId, todayIso);

  if (plan === "free" && usedToday >= 1) {
    return NextResponse.json(
      {
        error: "Free plan limit reached for today. Upgrade to Pro or Founding for more analyses.",
        plan,
        usedToday,
        limit: 1,
      },
      { status: 429 },
    );
  }

  const formData = await request.formData();
  const file = formData.get("file");
  const goal = formData.get("goal");

  if (!(file instanceof File)) {
    return NextResponse.json({ error: "A PDF file is required." }, { status: 400 });
  }

  if (file.type !== "application/pdf") {
    return NextResponse.json({ error: "Only PDF files are supported in this MVP." }, { status: 400 });
  }

  if (file.size > MAX_FILE_SIZE) {
    return NextResponse.json({ error: "PDF exceeds the 10 MB MVP limit." }, { status: 400 });
  }

  const fileBuffer = await file.arrayBuffer();
  const extracted = await extractPdfText(fileBuffer);

  const result = buildMockAnalysis({
    fileName: file.name,
    fileSizeKb: Math.max(1, Math.round(file.size / 1024)),
    targetOutcome: typeof goal === "string" ? goal : "Highlight the decision blockers and next step.",
  });

  if (extracted.parseMode === "real") {
    const lowerText = extracted.text.toLowerCase();
    const matchedMarkers = RISK_MARKERS.filter((marker) => lowerText.includes(marker));
    const sample = extracted.text.slice(0, 420);
    const confidenceBoost = matchedMarkers.length > 0 ? 7 : 3;

    result.parseMode = "real";
    result.textSample = sample;
    result.estimatedPages = extracted.numPages;
    result.confidence = Math.min(98, result.confidence + confidenceBoost);
    result.verdict = matchedMarkers.length >= 3 ? "Escalate for legal and pricing review" : "Proceed with targeted clarification";
    result.summary =
      sample.length > 120
        ? `Parser extracted source text successfully. Key review markers suggest ${matchedMarkers.length} potential risk signals that should be validated before commitment.`
        : "Parser extracted limited text. Document structure may be scan-based or image-heavy, so decision confidence is reduced.";
    result.insights = [
      `Risk markers found: ${matchedMarkers.length > 0 ? matchedMarkers.join(", ") : "none in keyword set"}.`,
      `Extracted text sample length: ${sample.length} characters across about ${extracted.numPages} pages.`,
      `Decision objective applied: ${result.targetOutcome}`,
    ];
  } else {
    result.parseMode = "mock";
  }

  await appendAnalysisHistory(result, userId);

  return NextResponse.json(
    {
      ...result,
      usage: {
        plan,
        usedToday: usedToday + 1,
        limit: plan === "free" ? 1 : null,
      },
    },
    { status: 200 },
  );
}
