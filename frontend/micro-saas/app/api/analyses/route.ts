import { NextResponse } from "next/server";

import { readAnalysisHistoryForUser } from "@/lib/analysis-history";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limitParam = Number(url.searchParams.get("limit") || "20");
  const limit = Number.isFinite(limitParam) ? Math.max(1, Math.min(100, limitParam)) : 20;
  const userId = request.headers.get("x-user-id")?.trim() || "anonymous";
  const entries = await readAnalysisHistoryForUser(userId, limit);

  return NextResponse.json(
    {
      userId,
      count: entries.length,
      entries,
    },
    { status: 200 },
  );
}
