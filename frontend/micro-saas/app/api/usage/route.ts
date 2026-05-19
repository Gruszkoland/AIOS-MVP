import { NextResponse } from "next/server";

import { countAnalysesForUserOnDate } from "@/lib/analysis-history";
import { resolvePlanTier } from "@/lib/entitlements";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const userId = request.headers.get("x-user-id")?.trim() || "anonymous";
  const todayIso = new Date().toISOString().slice(0, 10);
  const plan = await resolvePlanTier(userId);
  const usedToday = await countAnalysesForUserOnDate(userId, todayIso);

  return NextResponse.json(
    {
      userId,
      plan,
      usedToday,
      remainingToday: plan === "free" ? Math.max(0, 1 - usedToday) : null,
      limit: plan === "free" ? 1 : null,
    },
    { status: 200 },
  );
}
